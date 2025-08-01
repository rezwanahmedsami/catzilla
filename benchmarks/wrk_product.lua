-- Lua script for wrk to test product validation
wrk.method = "POST"
wrk.body = '{"name": "MacBook Pro", "price": "1299.99", "description": "Apple MacBook Pro", "sku": "MBP-13-001", "category": "electronics", "in_stock": true, "stock_quantity": 50, "tags": ["laptop", "apple"]}'
wrk.headers["Content-Type"] = "application/json"
