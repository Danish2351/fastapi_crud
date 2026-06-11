from fastapi import FastAPI, HTTPException, status  
import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv
from database import ProductCreate, PriceUpdate, SupplierCreate

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

app = FastAPI(
    title="FastAPI CRUD API",
    description="A simple API for crud operation."
)


def get_db_conn():
    return psycopg.connect(**DB_PARAMS, row_factory=dict_row)


# CREATE Product (POST)
@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Verify supplier existence if supplier_id is provided
                if product.supplier_id is not None:
                    cur.execute("SELECT supplier_id FROM suppliers WHERE supplier_id = %s", (product.supplier_id,))
                    if not cur.fetchone():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Supplier with ID {product.supplier_id} does not exist"
                        )
                
                cur.execute("""
                    INSERT INTO products (product_name, supplier_id, category_id, unit_price, units_in_stock, discontinued) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *;
                """, (
                    product.product_name,
                    product.supplier_id,
                    product.category_id,
                    product.unit_price,
                    product.units_in_stock,
                    product.discontinued
                ))
                inserted = cur.fetchone()
                return {"message": "Product created successfully", "data": inserted}
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

# READ ALL Products (GET ALL)
@app.get("/products", status_code=status.HTTP_200_OK)
def read_all_products():
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT product_id, product_name, quantity_per_unit, units_in_stock from products;")
                results = cur.fetchall()
                return results
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

# READ specific product's stock (GET)
@app.get("/products/stock/{product_name}", status_code=status.HTTP_200_OK)
def read_product_stock(product_name: str):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT product_id, product_name, quantity_per_unit, units_in_stock from products where product_name = %s;",
                    (product_name,)
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
                return row
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

# READ suppliers, their products, prices, and stock (GET)
@app.get("/suppliers/products", status_code=status.HTTP_200_OK)
def read_suppliers_products():
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        s.company_name AS supplier_name,
                        s.contact_name,
                        p.product_name,
                        p.unit_price,
                        p.units_in_stock
                    FROM suppliers s
                    JOIN products p ON s.supplier_id = p.supplier_id
                    ORDER BY p.product_name;
                """)
                results = cur.fetchall()
                return results
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

# UPDATE Price (PUT)
@app.put("/products/{product_id}/price", status_code=status.HTTP_200_OK)
def update_product_price(product_id: int, price_update: PriceUpdate):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
                if not cur.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product with ID {product_id} not found"
                    )
                
                cur.execute("""
                    UPDATE products 
                    SET unit_price = %s 
                    WHERE product_id = %s
                    RETURNING product_name, unit_price;
                """, (price_update.unit_price, product_id))
                updated = cur.fetchone()
                return {"message": "Price updated successfully", "data": updated}
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

# DELETE Supplier (Safely disconnects products and deletes supplier) (DELETE)
@app.delete("/suppliers/{supplier_id}", status_code=status.HTTP_200_OK)
def delete_supplier(supplier_id: int):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Check if supplier exists
                cur.execute("SELECT supplier_id FROM suppliers WHERE supplier_id = %s", (supplier_id,))
                if not cur.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Supplier with ID {supplier_id} not found"
                    )
                
                # 1. Disconnect products from the supplier
                cur.execute("""
                    UPDATE products 
                    SET supplier_id = NULL 
                    WHERE supplier_id = %s;
                """, (supplier_id,))
                
                # 2. Delete the supplier safely
                cur.execute("""
                    DELETE FROM suppliers 
                    WHERE supplier_id = %s;
                """, (supplier_id,))
                
                return {"message": f"Supplier {supplier_id} deleted successfully and products disconnected"}
    except psycopg.OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )