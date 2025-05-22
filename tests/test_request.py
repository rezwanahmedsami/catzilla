"""
Tests for Request class features
"""

import json
import pytest
from catzilla.types import Request


# def test_json_method():
#     # Test with valid JSON
#     request = Request(
#         method="POST",
#         path="/test",
#         body='{"key": "value"}',
#         client=None
#     )
#     assert request.json() == {"key": "value"}

#     # Test with empty body
#     request = Request(method="POST", path="/test", body="", client=None)
#     assert request.json() == {}

#     # Test with invalid JSON
#     request = Request(method="POST", path="/test", body="invalid json", client=None)
#     assert request.json() == {}


# def test_form_method():
#     # Test with valid form data
#     request = Request(
#         method="POST",
#         path="/test",
#         body="key1=value1&key2=value2",
#         client=None,
#         headers={"content-type": "application/x-www-form-urlencoded"}
#     )
#     assert request.form() == {"key1": "value1", "key2": "value2"}

#     # Test with empty body
#     request = Request(
#         method="POST",
#         path="/test",
#         body="",
#         client=None,
#         headers={"content-type": "application/x-www-form-urlencoded"}
#     )
#     assert request.form() == {}

#     # Test with wrong content type
#     request = Request(
#         method="POST",
#         path="/test",
#         body="key1=value1",
#         client=None,
#         headers={"content-type": "application/json"}
#     )
#     assert request.form() == {}


def test_client_ip():
    # Test with X-Forwarded-For
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=None,
        headers={"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
    )
    assert request.client_ip == "192.168.1.1"

    # Test with X-Real-IP
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=None,
        headers={"x-real-ip": "192.168.1.2"}
    )
    assert request.client_ip == "192.168.1.2"

    # Test fallback
    request = Request(method="GET", path="/test", body="", client=None)
    assert request.client_ip == "0.0.0.0"  # Fallback value when no IP available


# def test_content_type():
#     # Test basic content type
#     request = Request(
#         method="POST",
#         path="/test",
#         body="",
#         client=None,
#         headers={"content-type": "application/json"}
#     )
#     assert request.content_type == "application/json"

#     # Test with charset parameter
#     request = Request(
#         method="POST",
#         path="/test",
#         body="",
#         client=None,
#         headers={"content-type": "text/html; charset=utf-8"}
#     )
#     assert request.content_type == "text/html"

#     # Test with no content type
#     request = Request(method="POST", path="/test", body="", client=None)
#     assert request.content_type == ""


# def test_text():
#     # Test with UTF-8 text
#     request = Request(
#         method="POST",
#         path="/test",
#         body="Hello, World!",
#         client=None
#     )
#     assert request.text == "Hello, World!"

#     # Test with empty body
#     request = Request(method="POST", path="/test", body="", client=None)
    assert request.text == ""


def test_headers_normalization():
    # Test header key normalization
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=None,
        headers={
            "Content-Type": "application/json",
            "X-Custom-Header": "value"
        }
    )
    assert request.headers["content-type"] == "application/json"
    assert request.headers["x-custom-header"] == "value"


# def test_query_params():
#     # Test query parameters
#     request = Request(
#         method="GET",
#         path="/test",
#         body="",
#         client=None,
#         query_params={"name": "test", "value": "123"}
#     )
#     assert request.query_params == {"name": "test", "value": "123"}
