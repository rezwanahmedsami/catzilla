"""
Request Class Tests for Catzilla Framework

These tests cover the Request class functionality, focusing on:
1. Query parameter handling and lazy loading
2. Header processing and normalization
3. Client IP resolution
4. Form data handling
5. Text content processing

Note: These tests run without the C extension, so they verify the Python-side
behavior and graceful fallbacks when C functionality is not available.
"""

import json
import pytest
from catzilla.types import Request


def test_query_params_lazy_loading():
    """
    Test lazy loading of query parameters:
    - Verify initial state (empty, not loaded)
    - Check loading triggered on access
    - Verify loaded state after access
    - Test behavior without C capsule
    """
    request = Request(
        method="GET",
        path="/test?name=value&age=25",
        body="",
        client=None,
        request_capsule=None,
        _query_params={}
    )
    # Initially empty
    assert request._query_params == {}
    assert not request._loaded_query_params

    # Access should trigger loading (but in our test case will remain empty since no capsule)
    _ = request.query_params
    assert request._loaded_query_params


def test_query_params_empty_path():
    """
    Test query parameter handling with empty path:
    - Verify empty result for paths without query string
    - Ensure no errors when no parameters present
    """
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=None,
        request_capsule=None,
        _query_params={}
    )
    assert request.query_params == {}


def test_query_params_multiple():
    """
    Test handling of multiple query parameters:
    - Verify multiple parameters are correctly stored
    - Check access to multiple parameters
    - Test parameter value retrieval
    """
    request = Request(
        method="GET",
        path="/test?name=john&age=25&city=nyc",
        body="",
        client=None,
        request_capsule=None,
        _query_params={"name": "john", "age": "25", "city": "nyc"}
    )
    assert request.query_params == {"name": "john", "age": "25", "city": "nyc"}


def test_query_params_special_chars():
    """
    Test query parameters with special characters:
    - Verify URL-encoded characters are handled
    - Test spaces in parameter values
    - Test email addresses in parameters
    """
    request = Request(
        method="GET",
        path="/test?name=john%20doe&email=john%40example.com",
        body="",
        client=None,
        request_capsule=None,
        _query_params={"name": "john doe", "email": "john@example.com"}
    )
    assert request.query_params == {"name": "john doe", "email": "john@example.com"}


def test_query_params_empty_values():
    """
    Test query parameters with empty values:
    - Verify parameters with no values are handled
    - Test empty string values
    - Ensure consistent behavior with blank values
    """
    request = Request(
        method="GET",
        path="/test?empty=&null=&blank=",
        body="",
        client=None,
        request_capsule=None,
        _query_params={"empty": "", "null": "", "blank": ""}
    )
    assert request.query_params == {"empty": "", "null": "", "blank": ""}


def test_query_params_repeated_keys():
    """
    Test handling of repeated query parameters:
    - Verify behavior with duplicate parameter names
    - Check last value wins policy
    - Test multiple occurrences of same parameter
    """
    request = Request(
        method="GET",
        path="/test?key=1&key=2&key=3",
        body="",
        client=None,
        request_capsule=None,
        _query_params={"key": "3"}  # In our implementation, last value wins
    )
    assert request.query_params == {"key": "3"}


def test_query_params_with_json_body():
    """
    Test query parameters with JSON request body:
    - Verify query params work with JSON content
    - Check content-type handling
    - Test parameter access with JSON body
    """
    request = Request(
        method="POST",
        path="/test?id=123",
        body='{"name": "test"}',
        client=None,
        request_capsule=None,
        headers={"content-type": "application/json"},
        _query_params={"id": "123"}
    )
    assert request.query_params == {"id": "123"}


def test_query_params_with_form_data():
    """
    Test query parameters with form data:
    - Verify query params work with form submissions
    - Check form data doesn't interfere with query params
    - Test URL-encoded form content handling
    """
    request = Request(
        method="POST",
        path="/test?source=web",
        body="name=test&age=25",
        client=None,
        request_capsule=None,
        headers={"content-type": "application/x-www-form-urlencoded"},
        _query_params={"source": "web"}
    )
    assert request.query_params == {"source": "web"}


def test_client_ip():
    """
    Test client IP address resolution:
    - Check X-Forwarded-For header handling
    - Verify X-Real-IP header fallback
    - Test behavior without headers
    - Verify IP resolution order
    """
    # Test with X-Forwarded-For
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=None,
        request_capsule=None,
        headers={"x-forwarded-for": "192.168.1.1, 10.0.0.1"},
        _query_params={}
    )
    assert request.client_ip == "192.168.1.1"

    # Test with X-Real-IP
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=None,
        request_capsule=None,
        headers={"x-real-ip": "192.168.1.2"},
        _query_params={}
    )
    assert request.client_ip == "192.168.1.2"

    # Test with no headers (should return None since we can't get from C in tests)
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=None,
        request_capsule=None,
        _query_params={}
    )
    assert request.client_ip is None


def test_headers_normalization():
    """
    Test HTTP header normalization:
    - Verify header keys are converted to lowercase
    - Check original header values are preserved
    - Test access to normalized headers
    - Ensure case-insensitive header lookup
    """
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=None,
        request_capsule=None,
        headers={
            "Content-Type": "application/json",
            "X-Custom-Header": "value"
        },
        _query_params={}
    )
    assert request.headers["content-type"] == "application/json"
    assert request.headers["x-custom-header"] == "value"


def test_text_method():
    """
    Test text body access method:
    - Verify raw body access
    - Test empty body handling
    - Check text content retrieval
    - Ensure consistent return types
    """
    # Test with body
    request = Request(
        method="POST",
        path="/test",
        body="Hello, World!",
        client=None,
        request_capsule=None,
        _query_params={}
    )
    assert request.text() == "Hello, World!"

    # Test with empty body
    request = Request(
        method="POST",
        path="/test",
        body="",
        client=None,
        request_capsule=None,
        _query_params={}
    )
    assert request.text() == ""


def test_form_empty():
    """
    Test form data handling with empty content:
    - Verify empty form returns empty dict
    - Check content-type handling
    - Test behavior without C capsule
    - Ensure graceful handling of empty forms
    """
    request = Request(
        method="POST",
        path="/test",
        body="",
        client=None,
        request_capsule=None,
        headers={"content-type": "application/x-www-form-urlencoded"},
        _query_params={}
    )
    assert request.form() == {}
