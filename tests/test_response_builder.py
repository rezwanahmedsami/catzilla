"""Tests for the ResponseBuilder class."""

import pytest
from catzilla.response import response, ResponseBuilder
from catzilla.types import JSONResponse, HTMLResponse, Response

def test_response_builder_json():
    """Test JSON response building with status code."""
    resp = response.status(201).json({"ok": True})
    assert isinstance(resp, JSONResponse)
    assert resp.status_code == 201
    assert resp.body == {"ok": True}

def test_response_builder_html():
    """Test HTML response building."""
    html = "<h1>Hello</h1>"
    resp = response.html(html)
    assert isinstance(resp, HTMLResponse)
    assert resp.status_code == 200  # Default status
    assert resp.body == html

def test_response_builder_send():
    """Test plain text response building."""
    text = "Hello, plain text"
    resp = response.send(text)
    assert isinstance(resp, Response)
    assert resp.status_code == 200
    assert resp.body == text
    assert resp.content_type == "text/plain"

def test_response_builder_headers():
    """Test setting custom headers."""
    resp = (response
        .status(201)
        .set_header("X-Custom", "value")
        .json({"ok": True}))

    assert resp.headers["X-Custom"] == "value"
    assert resp.status_code == 201

def test_response_builder_cookies():
    """Test setting cookies."""
    resp = (response
        .set_cookie("session", "abc123", httponly=True)
        .set_cookie("theme", "dark")
        .json({"ok": True}))

    # Verify cookies were set
    cookies = getattr(resp, '_cookies', [])
    assert len(cookies) == 2
    assert any(c["name"] == "session" and c["httponly"] for c in cookies)
    assert any(c["name"] == "theme" and c["value"] == "dark" for c in cookies)

def test_response_builder_chaining():
    """Test method chaining with all features."""
    resp = (response
        .status(201)
        .set_header("X-API-Version", "1.0")
        .set_cookie("session", "abc123")
        .set_cookie("theme", "dark")
        .json({"created": True}))

    assert resp.status_code == 201
    assert resp.headers["X-API-Version"] == "1.0"
    assert resp.body == {"created": True}
    cookies = getattr(resp, '_cookies', [])
    assert len(cookies) == 2
