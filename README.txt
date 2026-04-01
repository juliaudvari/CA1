Inventory Management API - Endpoints Reference
=============================================

Base URL: http://localhost:8000
Interactive API docs: http://localhost:8000/docs

Endpoints:
----------
1. GET  /getSingleProduct?id=<ProductID>
   - Returns single product by ID
   - Param: id (int, required)

2. GET  /getAll
   - Returns all products in JSON format

3. POST /addNew
   - Adds new product (JSON body)
   - Body: {"ProductID": int, "Name": str, "UnitPrice": float, "StockQuantity": int, "Description": str}

4. DELETE /deleteOne?id=<ProductID>
   - Deletes product by ID
   - Param: id (int, required)

5. GET  /startsWith?letter=<char>
   - Returns products whose name starts with letter (e.g. s)
   - Param: letter (single char, required)

6. GET  /paginate?startId=<id>&endId=<id>
   - Returns batch of 10 products between start and end ID
   - Params: startId (int), endId (int), required

7. GET  /convert?id=<ProductID>
   - Returns product price in EUR (converted from USD via live exchange rate)
   - Param: id (int, required)

8. GET  /metrics
   - Prometheus metrics for API monitoring (A-grade)

FastAPI Documentation (interactive API docs): http://localhost:8000/docs
