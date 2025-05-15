from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models import Base, Item
from schemas import ItemCreate, ItemUpdate, ItemResponse
from database import engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/", response_model=List[ItemResponse])
def read_items(
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 10,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = None,
    sort_by: Optional[str] = None,   # e.g. "price,name"
    sort_order: Optional[str] = "asc", # e.g. "desc,asc"
    db: Session = Depends(get_db)
):
    query = db.query(Item).filter(Item.is_deleted == False)

    if search:
        query = query.filter(
            (Item.name.ilike(f"%{search}%")) | 
            (Item.description.ilike(f"%{search}%"))
        )

    if min_price is not None:
        query = query.filter(Item.price >= min_price)
    if max_price is not None:
        query = query.filter(Item.price <= max_price)
    if in_stock is not None:
        query = query.filter(Item.in_stock == in_stock)

    # Sorting support
    if sort_by:
        sort_fields = [field.strip() for field in sort_by.split(",")]
        sort_orders = [order.strip().lower() for order in sort_order.split(",")]
        while len(sort_orders) < len(sort_fields):
            sort_orders.append("asc")

        for field, order in reversed(list(zip(sort_fields, sort_orders))):
            column = getattr(Item, field, None)
            if not column or order not in {"asc", "desc"}:
                continue
            if order == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

    items = query.offset(skip).limit(limit).all()
    return items

@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id, Item.is_deleted == False).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item_update: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id, Item.is_deleted == False).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for key, value in item_update.dict().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item

@app.delete("/items/{item_id}")
def soft_delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id, Item.is_deleted == False).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.is_deleted = True
    db.commit()
    return {"message": "Item soft-deleted"}

@app.get("/items/deleted", response_model=List[ItemResponse])
def read_deleted_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(Item).filter(Item.is_deleted == True).offset(skip).limit(limit).all()
    return items

@app.put("/items/{item_id}/restore", response_model=ItemResponse)
def restore_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id, Item.is_deleted == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or not deleted")
    item.is_deleted = False
    db.commit()
    db.refresh(item)
    return item
