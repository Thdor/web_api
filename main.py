from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# In-memory "database"
items_db = []

# Define a data model
class Item(BaseModel):
    name: str
    price: float
    description: str = None
    in_stock: bool = True

# Home route
@app.get("/")
def read_root():
    return {"message": "Welcome to the API!"}

# Create item
@app.post("/items/")
def create_item(item: Item):
    item_id = len(items_db)
    item_dict = item.dict()
    item_dict["id"] = item_id
    item_dict["is_deleted"] = False  # Soft delete flag
    items_db.append(item_dict)
    return {"message": "Item added", "item": item_dict}

# Get all non-deleted items
@app.get("/items/")
def get_all_items(
    search: Optional[str] = Query(None, description="Search keyword"),
    skip: int = Query(0, ge=0, description="Items to skip (for pagination)"),
    limit: int = Query(10, ge=1, le=100, description="Max number of items to return")
):
    # Filter only non-deleted items
    visible_items = [item for item in items_db if not item["is_deleted"]]

    # Apply search (if provided)
    if search:
        search = search.lower()
        visible_items = [
            item for item in visible_items
            if search in item["name"].lower() or
               (item.get("description") and search in item["description"].lower())
        ]

    # Apply pagination
    paginated_items = visible_items[skip: skip + limit]
    return {
        "total": len(visible_items),
        "skip": skip,
        "limit": limit,
        "items": paginated_items
    }
# Get deleted items only
@app.get("/items/deleted")
def get_deleted_items():
    deleted_items = [item for item in items_db if item["is_deleted"]]
    return {"deleted_items": deleted_items}
# Get item by ID
@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id < 0 or item_id >= len(items_db) or items_db[item_id]["is_deleted"]:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

# Update item (only if not deleted)
@app.put("/items/{item_id}")
def update_item(item_id: int, updated_item: Item):
    if item_id < 0 or item_id >= len(items_db) or items_db[item_id]["is_deleted"]:
        raise HTTPException(status_code=404, detail="Item not found")

    updated_data = updated_item.dict()
    updated_data["id"] = item_id
    updated_data["is_deleted"] = False
    items_db[item_id] = updated_data
    return {"message": "Item updated", "item": updated_data}

# Soft-delete item
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    if item_id < 0 or item_id >= len(items_db) or items_db[item_id]["is_deleted"]:
        raise HTTPException(status_code=404, detail="Item not found")

    items_db[item_id]["is_deleted"] = True
    return {"message": "Item soft-deleted", "item": items_db[item_id]}

# Restore a soft-deleted item
@app.put("/items/{item_id}/restore")
def restore_item(item_id: int):
    if item_id < 0 or item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="Item not found")

    if not items_db[item_id]["is_deleted"]:
        raise HTTPException(status_code=400, detail="Item is not deleted")

    items_db[item_id]["is_deleted"] = False
    return {"message": "Item restored", "item": items_db[item_id]}