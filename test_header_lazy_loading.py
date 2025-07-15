#!/usr/bin/env python3
"""
Test to verify lazy header loading functionality works correctly
"""

import pytest
from unittest.mock import MagicMock, patch
from catzilla.types import Request

def test_lazy_header_loading():
    """Test that headers are loaded lazily only when requested"""

    # Create a mock request capsule
    mock_request_capsule = MagicMock()

    # Create a request object with required arguments
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=MagicMock(),
        request_capsule=mock_request_capsule
    )
    request.headers = {}  # No pre-loaded headers

    # Mock the C get_header function to return test values
    with patch('catzilla._catzilla.get_header') as mock_get_header:
        mock_get_header.return_value = "TestValue123"

        # Call get_header - this should trigger the lazy loading
        result = request.get_header("User-Agent")

        # Verify the C function was called with correct parameters
        mock_get_header.assert_called_once_with(mock_request_capsule, "User-Agent")

        # Verify the result
        assert result == "TestValue123"

    print("✅ Lazy header loading test passed!")

def test_header_fallback():
    """Test that fallback to pre-loaded headers works when C function fails"""

    # Create a request with pre-loaded headers
    request = Request(
        method="GET",
        path="/test",
        body="",
        client=MagicMock(),
        request_capsule=MagicMock()
    )
    request.headers = {"user-agent": "FallbackAgent"}

    # Mock the C get_header function to raise an exception
    with patch('catzilla._catzilla.get_header') as mock_get_header:
        mock_get_header.side_effect = Exception("C function failed")

        # Call get_header - should fallback to pre-loaded headers
        result = request.get_header("User-Agent")

        # Verify the result came from fallback
        assert result == "FallbackAgent"

    print("✅ Header fallback test passed!")

if __name__ == "__main__":
    test_lazy_header_loading()
    test_header_fallback()
    print("🎉 All header tests passed!")
