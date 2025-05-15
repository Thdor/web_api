from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from models import Base, Item
from dotenv import load_dotenv
import os

load_dotenv()

# Load DB config
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")
DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

# Connect to the database
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
session = Session(bind=engine)

# Sample items to insert
items = [
    Item(name="Pieapple", description="Fresh Pieapple", price=1.9, in_stock=True),
    Item(name="Mango", description="Fresh Mango", price=1.8, in_stock=True),
    Item(name="Egg", description="Egg", price=4, in_stock=True),
    Item(name="Milk", description="Milk", price=3, in_stock=True),
    Item(name="Honey", description="Honey", price=2.6, in_stock=True),
    Item(name="Orange", description="Fresh Orange", price=1, in_stock=True),
    Item(name="Strawberry", description="Fresh Strawberry", price=2.2, in_stock=True),
    Item(name="Blueberry", description="Fresh Blueberry", price=3, in_stock=True),
    Item(name="Yogurt", description="Yogurt", price=1.5, in_stock=True),
    Item(name="Grape", description="Fresh Grape", price=1.3, in_stock=True),
    Item(name="Avocado", description="Fresh Avocado", price=1.6, in_stock=True)
]

# Insert if not already present
for item in items:
    existing = session.query(Item).filter_by(name=item.name).first()
    if not existing:
        session.add(item)

session.commit()
session.close()

print("Sample items inserted successfully!")