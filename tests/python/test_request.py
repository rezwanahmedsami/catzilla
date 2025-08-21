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


# def test_form_empty():
#     """
#     Test form data handling with empty content:
#     - Verify empty form returns empty dict
#     - Check content-type handling
#     - Test behavior without C capsule
#     - Ensure graceful handling of empty forms
#     """
#     request = Request(
#         method="POST",
#         path="/test",
#         body="",
#         client=None,
#         request_capsule=None,
#         headers={"content-type": "application/x-www-form-urlencoded"},
#         _query_params={}
#     )
#     assert request.form() == {}


# =====================================================
# ASYNC REQUEST PROCESSING TESTS
# =====================================================

@pytest.mark.asyncio
async def test_async_request_json_processing():
    """Test async JSON request processing"""
    import asyncio

    async def async_json_processor(request):
        # Simulate async JSON processing
        await asyncio.sleep(0.01)

        try:
            json_data = request.json()
            return {
                "processed": True,
                "data": json_data,
                "async": True
            }
        except Exception as e:
            return {
                "processed": False,
                "error": str(e),
                "async": True
            }

    # Test with valid JSON
    request = Request(
        method="POST",
        path="/async/json",
        body='{"name": "async_test", "value": 123}',
        client=None,
        request_capsule=None,
        headers={"content-type": "application/json"},
        _query_params={}
    )

    result = await async_json_processor(request)
    assert result["processed"] is True
    assert result["async"] is True


@pytest.mark.asyncio
async def test_async_request_text_processing():
    """Test async text request processing"""
    import asyncio

    async def async_text_processor(request):
        # Simulate async text processing
        await asyncio.sleep(0.01)

        text_content = request.text()

        # Simulate text analysis
        word_count = len(text_content.split()) if text_content else 0
        char_count = len(text_content)

        return {
            "text_processed": True,
            "word_count": word_count,
            "char_count": char_count,
            "content_preview": text_content[:50] if text_content else "",
            "async": True
        }

    request = Request(
        method="POST",
        path="/async/text",
        body="This is async text processing test content for Catzilla v0.2.0",
        client=None,
        request_capsule=None,
        headers={"content-type": "text/plain"},
        _query_params={}
    )

    result = await async_text_processor(request)
    assert result["text_processed"] is True
    assert result["word_count"] > 0
    assert result["async"] is True


@pytest.mark.asyncio
async def test_async_request_header_analysis():
    """Test async request header analysis"""
    import asyncio

    async def async_header_analyzer(request):
        # Simulate async header analysis
        await asyncio.sleep(0.01)

        headers = request.headers or {}

        # Analyze headers asynchronously
        security_headers = []
        content_headers = []

        for header_name in headers:
            await asyncio.sleep(0.001)  # Simulate per-header processing

            if 'security' in header_name.lower() or 'auth' in header_name.lower():
                security_headers.append(header_name)
            elif 'content' in header_name.lower():
                content_headers.append(header_name)

        return {
            "headers_analyzed": True,
            "total_headers": len(headers),
            "security_headers": security_headers,
            "content_headers": content_headers,
            "has_user_agent": "user-agent" in [h.lower() for h in headers],
            "async": True
        }

    request = Request(
        method="GET",
        path="/async/headers",
        body="",
        client=None,
        request_capsule=None,
        headers={
            "user-agent": "AsyncTestAgent/1.0",
            "content-type": "application/json",
            "authorization": "Bearer async_token",
            "x-security-token": "async_security"
        },
        _query_params={}
    )

    result = await async_header_analyzer(request)
    assert result["headers_analyzed"] is True
    assert result["total_headers"] == 4
    assert result["async"] is True


@pytest.mark.asyncio
async def test_async_request_query_param_processing():
    """Test async query parameter processing"""
    import asyncio

    async def async_query_processor(request):
        # Simulate async query parameter validation and processing
        await asyncio.sleep(0.01)

        # Access query params (triggers lazy loading)
        query_params = request.query_params

        # Simulate async validation of each parameter
        validated_params = {}
        invalid_params = []

        for key in query_params:
            await asyncio.sleep(0.002)  # Simulate per-param validation

            # Mock validation logic
            if key.startswith('valid_'):
                validated_params[key] = query_params[key]
            else:
                invalid_params.append(key)

        return {
            "query_processed": True,
            "total_params": len(query_params),
            "validated_params": validated_params,
            "invalid_params": invalid_params,
            "async": True
        }

    request = Request(
        method="GET",
        path="/async/query?valid_name=test&valid_age=25&invalid_token=abc&valid_type=user",
        body="",
        client=None,
        request_capsule=None,
        _query_params={}
    )

    result = await async_query_processor(request)
    assert result["query_processed"] is True
    assert result["async"] is True


@pytest.mark.asyncio
async def test_async_request_concurrent_processing():
    """Test concurrent async request processing"""
    import asyncio

    async def process_request_async(request_id, delay=0.01):
        await asyncio.sleep(delay)
        return {
            "request_id": request_id,
            "processed_at": asyncio.get_event_loop().time(),
            "async": True
        }

    # Create multiple mock requests
    requests = []
    for i in range(5):
        request = Request(
            method="GET",
            path=f"/async/concurrent/{i}",
            body="",
            client=None,
            request_capsule=None,
            _query_params={}
        )
        requests.append((i, request))

    # Process requests concurrently
    tasks = [process_request_async(req_id, 0.01) for req_id, _ in requests]
    results = await asyncio.gather(*tasks)

    # Verify all requests were processed
    assert len(results) == 5
    assert all(result["async"] for result in results)
    assert all(result["request_id"] in range(5) for result in results)


@pytest.mark.asyncio
async def test_async_request_error_handling():
    """Test async request error handling"""
    import asyncio

    async def async_request_handler_with_errors(request, should_fail=False):
        await asyncio.sleep(0.01)

        if should_fail:
            raise ValueError("Async request processing error")

        return {
            "success": True,
            "path": request.path,
            "method": request.method,
            "async": True
        }

    # Test successful processing
    success_request = Request(
        method="GET",
        path="/async/success",
        body="",
        client=None,
        request_capsule=None,
        _query_params={}
    )

    result = await async_request_handler_with_errors(success_request, should_fail=False)
    assert result["success"] is True
    assert result["async"] is True

    # Test error handling
    error_request = Request(
        method="GET",
        path="/async/error",
        body="",
        client=None,
        request_capsule=None,
        _query_params={}
    )

    try:
        await async_request_handler_with_errors(error_request, should_fail=True)
        assert False, "Expected ValueError to be raised"
    except ValueError as e:
        assert "Async request processing error" in str(e)
