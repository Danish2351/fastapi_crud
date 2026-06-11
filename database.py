from pydantic import BaseModel

class ProductCreate(BaseModel):
    product_name: str
    supplier_id: int | None = None
    category_id: int | None = None
    unit_price: float | None = None
    units_in_stock: int | None = None
    discontinued: int = 0

class PriceUpdate(BaseModel):
    unit_price: float

class SupplierCreate(BaseModel):
    company_name: str
    contact_name: str | None = None