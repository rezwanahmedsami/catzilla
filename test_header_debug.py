#!/usr/bin/env python3
"""
Simple header test to debug the issue
"""

from catzilla import Catzilla, Request, Response, JSONResponse

app = Catzilla()

@app.get("/test-header")
def test_header(request: Request) -> Response:
    """Test manual header extraction"""
    user_agent = request.get_header("User-Agent")
    authorization = request.get_header("Authorization")

    return JSONResponse({
        "user_agent": user_agent,
        "authorization": authorization,
        "all_headers": dict(request.headers) if hasattr(request, 'headers') else "No headers attribute"
    })

if __name__ == "__main__":
    app.listen(host="127.0.0.1", port=8001)
