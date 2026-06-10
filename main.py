from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status  
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv

load_dotenv()

db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_port = os.getenv("DB_PORT")
db_username = os.getenv("DB_USERNAME")

DB_PARAMS = {
    "host": db_host,
    "dbname": db_name,
    "user": db_username,
    "password": db_password,
    "port": db_port
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database table
    try:
        with psycopg.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS items (
                        id INT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        price FLOAT NOT NULL
                    );
                """)
    except psycopg.OperationalError as e:
        print(f"Database connection failed during startup: {e}")
    yield

app = FastAPI(
    title="FastAPI CRUD API",
    description="A simple API for crud operation.",
    lifespan=lifespan
)

class Item(BaseModel):
    name: str
    description: str|None = None
    price: float

def get_db_conn():
    return psycopg.connect(**DB_PARAMS, row_factory=dict_row)

# CREATE
@app.post("/items/{item_id}", status_code=201)
def create_item(item_id: int, item: Item):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM items WHERE id = %s", (item_id,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail="Item already exists")
                cur.execute(
                    "INSERT INTO items (id, name, description, price) VALUES (%s, %s, %s, %s) RETURNING *",
                    (item_id, item.name, item.description, item.price)
                )
                inserted = cur.fetchone()
                return {"message": "Item created successfully", "data": inserted}
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

# READ (All)
@app.get("/items/all", status_code=status.HTTP_200_OK)
def read_all_items():
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM items")
                results = cur.fetchall()
                # Return dictionary formatted as {id: {name, description, price}} to match original signature
                return {
                    row["id"]: {
                        "name": row["name"],
                        "description": row["description"],
                        "price": row["price"]
                    }
                    for row in results
                }
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

# READ (Single)
@app.get("/items/{item_id}", status_code=status.HTTP_200_OK)
def read_item(item_id: int):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, description, price FROM items WHERE id = %s", (item_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Item not found")
                return row
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

# UPDATE
@app.put("/items/{item_id}", status_code=status.HTTP_200_OK)
def update_item(item_id: int, item: Item):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM items WHERE id = %s", (item_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Item not found")
                cur.execute(
                    "UPDATE items SET name = %s, description = %s, price = %s WHERE id = %s RETURNING name, description, price",
                    (item.name, item.description, item.price, item_id)
                )
                updated = cur.fetchone()
                return {"message": "Item updated successfully", "data": updated}
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

# DELETE
@app.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
def delete_item(item_id: int):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM items WHERE id = %s", (item_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Item not found")
                cur.execute("DELETE FROM items WHERE id = %s", (item_id,))
                return {"message": f"Item {item_id} deleted successfully"}
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )