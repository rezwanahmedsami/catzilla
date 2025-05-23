# tests/python/test_basic.py
"""
Basic tests for Catzilla framework core functionality.
These tests cover the fundamental components:
1. Response classes (HTML, JSON)
2. Basic request handling
3. Route registration
4. JSON parsing behavior without C layer
"""

import pytest
from catzilla import Request, Response, JSONResponse, HTMLResponse, App


def test_html_response():
    """
    Test HTMLResponse class functionality:
    - Verify correct status code (200 by default)
    - Verify content type is set to text/html
    - Verify body contains the provided HTML
    """
    html = "<h1>Hello</h1>"
    resp = HTMLResponse(html)
    assert resp.status_code == 200
    assert resp.content_type == "text/html"
    assert resp.body == html


def test_json_response():
    """
    Test JSONResponse class functionality:
    - Verify correct status code (200 by default)
    - Verify content type is set to application/json
    - Verify body is properly JSON serialized
    """
    data = {"key": "value"}
    resp = JSONResponse(data)
    assert resp.status_code == 200
    assert resp.content_type == "application/json"
    assert resp.body == '{"key": "value"}'


def test_custom_status_code():
    """
    Test custom status code in responses:
    - Verify custom status code (404) is properly set
    - Verify response body still contains the correct data
    """
    data = {"error": "not found"}
    resp = JSONResponse(data, status_code=404)
    assert resp.status_code == 404
    assert "not found" in resp.body


def test_request_json_parsing_valid():
    """
    Test JSON parsing with valid JSON input:
    - Without C capsule, should return empty dict
    - Tests the fallback behavior when C layer is not available
    - Verifies content-type header is properly handled
    """
    req = Request(
        method="POST",
        path="/",
        body='{"a": 123}',
        client=None,
        request_capsule=None,
        headers={"content-type": "application/json"},
        _query_params={}
    )
    assert req.json() == {}  # Will be empty since no C capsule in test


def test_request_json_parsing_empty():
    """
    Test JSON parsing with empty body:
    - Verify empty body returns empty dict
    - Ensures no errors when parsing empty content
    """
    req = Request(
        method="POST",
        path="/",
        body="",
        client=None,
        request_capsule=None,
        headers={"content-type": "application/json"},
        _query_params={}
    )
    assert req.json() == {}


def test_request_json_parsing_invalid():
    """
    Test JSON parsing with invalid JSON:
    - Verify invalid JSON returns empty dict
    - Ensures graceful handling of malformed JSON
    """
    req = Request(
        method="POST",
        path="/",
        body="{not: valid}",
        client=None,
        request_capsule=None,
        headers={"content-type": "application/json"},
        _query_params={}
    )
    assert req.json() == {}


def test_app_route_registration():
    """
    Test route registration in App:
    - Verify routes are properly registered
    - Check HTTP method mapping
    - Verify handler function is stored correctly
    - Test basic routing functionality
    """
    app = App()

    @app.get("/hello")
    def hello(req):
        return HTMLResponse("<h1>Hi</h1>")

    assert "GET" in app.router.routes
    assert "/hello" in app.router.routes["GET"]
    assert callable(app.router.routes["GET"]["/hello"])
