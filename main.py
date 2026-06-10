from fastapi import FastAPI, HTTPException, status  
from pydantic import BaseModel
#from typing import Optional

app = FastAPI(title = "FastAPI CRUD API", description = "A simple API for managing books.")

db={}

class Item(BaseModel):
    name: str
    description: str|None = None
    price: float

# CREATE
@app.post("/items/{item_id}", status_code=201)
def create_item(item_id: int, item: Item):
    if item_id in db:
        raise HTTPException(status_code=400, detail="Item already exists")
    db[item_id] = item.dict()
    return {"message": "Item created successfully", "data": db[item_id]}

# READ (All)
@app.get("/items/all", status_code=status.HTTP_200_OK)
def read_all_items():
    return db

# READ (Single)
@app.get("/items/{item_id}", status_code=status.HTTP_200_OK)
def read_item(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    return db[item_id]

# UPDATE
@app.put("/items/{item_id}", status_code=status.HTTP_200_OK)
def update_item(item_id: int, item: Item):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    db[item_id] = item.dict()
    return {"message": "Item updated successfully", "data": db[item_id]}

# DELETE
@app.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
def delete_item(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    del db[item_id]
    return {"message": f"Item {item_id} deleted successfully"}