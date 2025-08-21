-- Lua script for wrk to test simple user validation
wrk.method = "POST"
wrk.body = '{"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30}'
wrk.headers["Content-Type"] = "application/json"
