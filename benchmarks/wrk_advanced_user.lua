-- Lua script for wrk to test advanced user validation
wrk.method = "POST"
wrk.body = '{"id": 1, "username": "janesmith", "email": "jane@example.com", "age": 28, "height": 1.65, "is_active": true, "tags": ["developer", "python"], "metadata": {"dept": "eng"}}'
wrk.headers["Content-Type"] = "application/json"
