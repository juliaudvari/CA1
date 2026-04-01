import csv
import json
import os
from pymongo import MongoClient

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "inventory_db"
COLLECTION_NAME = "products"
CSV_FILE = "products.csv"


def convert_csv_to_json(csv_path: str) -> list[dict]:
    """Read CSV and convert to list of JSON-compatible dicts"""
    products = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product = {
                "ProductID": int(row["ProductID"]),
                "Name": row["Name"],
                "UnitPrice": float(row["UnitPrice"]),
                "StockQuantity": int(row["StockQuantity"]),
                "Description": row["Description"],
            }
            products.append(product)
    return products


def import_to_mongodb(products: list[dict]) -> None:
    """Insert products into MongoDB, replacing existing collection"""
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Clear existing data and insert fresh
    collection.delete_many({})
    collection.insert_many(products)

    # Create index on ProductID for fast lookups
    collection.create_index("ProductID", unique=True)

    print(f"Successfully imported {len(products)} products to MongoDB")
    client.close()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, CSV_FILE)

    if not os.path.exists(csv_path):
        print(f"Error: {CSV_FILE} not found at {csv_path}")
        return

    products = convert_csv_to_json(csv_path)
    import_to_mongodb(products)


if __name__ == "__main__":
    main()
