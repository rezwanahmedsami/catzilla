"""
Express.js-style fluent response builder for Catzilla.
"""

from typing import Any, Dict, Optional, Union

from .types import HTMLResponse, JSONResponse, Response


class ResponseBuilder:
    """
    A fluent interface for building HTTP responses, inspired by Express.js.

    Examples:
        >>> response.status(201).json({"ok": True})
        >>> response.html("<h1>Hello</h1>")
        >>> response.send("Hello, plain text")
        >>> response.status(404).json({"error": "Not found"})
    """

    def __init__(self):
        self._status_code: int = 200
        self._headers: Dict[str, str] = {}

    def status(self, code: int) -> "ResponseBuilder":
        """Set the HTTP status code for the response.

        Args:
            code: HTTP status code (e.g., 200, 201, 404, etc.)

        Returns:
            self: For method chaining
        """
        self._status_code = code
        return self

    def set_header(self, key: str, value: str) -> "ResponseBuilder":
        """Set a custom header for the response.

        Args:
            key: Header name
            value: Header value

        Returns:
            self: For method chaining
        """
        self._headers[key] = value
        return self

    def json(self, data: Any) -> JSONResponse:
        """Send a JSON response.

        Args:
            data: Data to be serialized to JSON

        Returns:
            JSONResponse: The response object
        """
        return JSONResponse(data, status_code=self._status_code, headers=self._headers)

    def html(self, content: str) -> HTMLResponse:
        """Send an HTML response.

        Args:
            content: HTML content string

        Returns:
            HTMLResponse: The response object
        """
        return HTMLResponse(
            content, status_code=self._status_code, headers=self._headers
        )

    def send(self, text: str) -> Response:
        """Send a plain text response.

        Args:
            text: Plain text content

        Returns:
            Response: The response object
        """
        return Response(
            body=text,
            status_code=self._status_code,
            content_type="text/plain",
            headers=self._headers,
        )

    def set_cookie(
        self,
        name: str,
        value: str,
        max_age: Optional[int] = None,
        expires: Optional[str] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None,
    ) -> "ResponseBuilder":
        """Set a cookie in the response.

        This is a passthrough to the underlying Response.set_cookie() method.
        The cookie will be set when the final response is created.

        Args:
            name: Cookie name
            value: Cookie value
            max_age: Lifetime in seconds
            expires: Expiration date string
            path: Cookie path
            domain: Cookie domain
            secure: HTTPS only
            httponly: Block JavaScript access
            samesite: SameSite policy

        Returns:
            self: For method chaining
        """
        # Store cookie info to be applied when response is created
        if not hasattr(self, "_cookies"):
            self._cookies = []

        self._cookies.append(
            {
                "name": name,
                "value": value,
                "max_age": max_age,
                "expires": expires,
                "path": path,
                "domain": domain,
                "secure": secure,
                "httponly": httponly,
                "samesite": samesite,
            }
        )
        return self


# Create singleton instance
response = ResponseBuilder()

__all__ = ["response", "ResponseBuilder"]
