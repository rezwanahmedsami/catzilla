# tests/python/test_basic.py

import pytest
from catzilla import Request, Response, JSONResponse, HTMLResponse, App


def test_html_response():
    html = "<h1>Hello</h1>"
    resp = HTMLResponse(html)
    assert resp.status_code == 200
    assert resp.content_type == "text/html"
    assert resp.body == html


def test_json_response():
    data = {"key": "value"}
    resp = JSONResponse(data)
    assert resp.status_code == 200
    assert resp.content_type == "application/json"
    assert resp.body == '{"key": "value"}'


def test_custom_status_code():
    data = {"error": "not found"}
    resp = JSONResponse(data, status_code=404)
    assert resp.status_code == 404
    assert "not found" in resp.body


def test_request_json_parsing_valid():
    req = Request(method="POST", path="/", body='{"a": 123}', client=None)
    assert req.json == {"a": 123}


def test_request_json_parsing_empty():
    req = Request(method="POST", path="/", body="", client=None)
    assert req.json == {}


def test_request_json_parsing_invalid():
    req = Request(method="POST", path="/", body="{not: valid}", client=None)
    assert req.json == {}


def test_app_route_registration():
    app = App()

    @app.get("/hello")
    def hello(req):
        return HTMLResponse("<h1>Hi</h1>")

    assert "GET" in app.router.routes
    assert "/hello" in app.router.routes["GET"]
    assert callable(app.router.routes["GET"]["/hello"])
