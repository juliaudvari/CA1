import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo import MongoClient
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# MongoDB config
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "inventory_db"
COLLECTION_NAME = "products"

# Prometheus metrics (API monitoring)
REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds",
    "API request latency in seconds",
    ["endpoint"]
)


# Pydantic models for validation
class Product(BaseModel):
    ProductID: int = Field(..., gt=0, description="Unique product identifier")
    Name: str = Field(..., min_length=1, max_length=200)
    UnitPrice: float = Field(..., ge=0)
    StockQuantity: int = Field(..., ge=0)
    Description: str = Field(..., min_length=1)


class ProductCreate(BaseModel):
    ProductID: int = Field(..., gt=0)
    Name: str = Field(..., min_length=1, max_length=200)
    UnitPrice: float = Field(..., ge=0)
    StockQuantity: int = Field(..., ge=0)
    Description: str = Field(..., min_length=1)


def get_db():
    client = MongoClient(MONGODB_URI)
    return client[DATABASE_NAME][COLLECTION_NAME]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup and check MongoDB connection
    try:
        get_db().find_one()
    except Exception as e:
        print(f"Warning: MongoDB connection failed: {e}")
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Inventory Management API",
    description="Complete API for product inventory management",
    version="1.0.0",
    lifespan=lifespan,
)


# Middleware for Prometheus metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    import time
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    return response


@app.get("/getSingleProduct")
async def get_single_product(
    id: int = Query(..., gt=0, description="Product ID")
):
    """Return a single product by ID"""
    product = get_db().find_one({"ProductID": id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["_id"] = str(product["_id"])
    return product


@app.get("/getAll")
async def get_all():
    """Return all products in the inventory"""
    products = list(get_db().find({}))
    for p in products:
        p["_id"] = str(p["_id"])
    return products


@app.post("/addNew")
async def add_new(product: ProductCreate):
    """Add a new product to the inventory"""
    db = get_db()
    if db.find_one({"ProductID": product.ProductID}):
        raise HTTPException(status_code=400, detail="Product ID already exists")
    doc = product.model_dump()
    db.insert_one(doc)
    return {"message": "Product added successfully", "ProductID": product.ProductID}


@app.delete("/deleteOne")
async def delete_one(
    id: int = Query(..., gt=0, description="Product ID to delete")
):
    """Delete a product by ID"""
    result = get_db().delete_one({"ProductID": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


@app.get("/startsWith")
async def starts_with(
    letter: str = Query(..., min_length=1, max_length=1, description="Letter to filter by")
):
    """Return all products whose name starts with the given letter"""
    letter = letter.upper()
    products = list(get_db().find({
        "Name": {"$regex": f"^{letter}", "$options": "i"}
    }))
    for p in products:
        p["_id"] = str(p["_id"])
    return products


@app.get("/paginate")
async def paginate(
    start_id: int = Query(..., gt=0, alias="startId", description="Starting product ID"),
    end_id: int = Query(..., gt=0, alias="endId", description="Ending product ID")
):
    """Return products in batches of 10 between start and end ID"""
    if start_id > end_id:
        raise HTTPException(status_code=400, detail="startId must be <= endId")
    products = list(get_db().find(
        {"ProductID": {"$gte": start_id, "$lte": end_id}}
    ).sort("ProductID", 1).limit(10))
    for p in products:
        p["_id"] = str(p["_id"])
    return products


@app.get("/convert")
async def convert(
    id: int = Query(..., gt=0, description="Product ID to get price in EUR")
):
    """Return the product's price converted from USD to EUR"""
    product = get_db().find_one({"ProductID": id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Exchange rate API unavailable")
        data = resp.json()
        rate = data["rates"]["EUR"]

    price_usd = product["UnitPrice"]
    price_eur = round(price_usd * rate, 2)
    return {
        "ProductID": id,
        "Name": product["Name"],
        "PriceUSD": price_usd,
        "PriceEUR": price_eur,
        "ExchangeRate": rate,
    }


# Prometheus metrics endpoint for API monitoring
@app.get("/metrics")
async def metrics():
    """Prometheus metrics for API performance monitoring"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
