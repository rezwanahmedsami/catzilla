"""
Type definitions for Catzilla
"""

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from urllib.parse import parse_qs


@dataclass
class Request:
    """HTTP Request object"""

    method: str
    path: str
    body: str
    client: Any  # The client capsule from C
    request_capsule: Any  # The request capsule from C
    headers: Dict[str, str] = None
    _query_params: Dict[str, str] = None  # Internal storage for query params
    _client_ip: Optional[str] = None
    _parsed_form: Optional[Dict[str, str]] = None
    _text: Optional[str] = None
    _json: Optional[Any] = None
    _content_type: Optional[str] = None
    _loaded_query_params: bool = False

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self._query_params is None:
            self._query_params = {}

        # Normalize header keys to lowercase for consistent access
        self.headers = {k.lower(): v for k, v in self.headers.items()}

    @property
    def query_params(self) -> Dict[str, str]:
        """Lazily load query parameters from C when accessed"""
        if not self._loaded_query_params:
            try:
                from catzilla._catzilla import get_query_param

                # Try to get each parameter from the query string
                if "?" in self.path:
                    query_string = self.path.split("?", 1)[1]
                    for pair in query_string.split("&"):
                        if "=" in pair:
                            key = pair.split("=", 1)[0]
                            value = get_query_param(self.request_capsule, key)
                            if value is not None:
                                print(
                                    f"[DEBUG-PY] Got query param from C: {key}={value}"
                                )
                                self._query_params[key] = value
                self._loaded_query_params = True
            except Exception as e:
                print(f"[DEBUG-PY] Error loading query params from C: {e}")
                self._loaded_query_params = True  # Don't try again even if failed
        return self._query_params

    @query_params.setter
    def query_params(self, value: Dict[str, str]):
        """Set query parameters"""
        self._query_params = value

    def json(self) -> Any:
        """Parse body as JSON"""
        if self._json is None:
            try:
                from catzilla._catzilla import get_json, parse_json

                print(
                    f"[DEBUG-PY] Attempting to parse JSON with content type: {self.content_type}"
                )
                if self.content_type == "application/json":
                    # Try to get the JSON directly first, since it might be pre-parsed
                    result = get_json(self.request_capsule)
                    if result is not None:
                        self._json = result
                        print(
                            f"[DEBUG-PY] Got pre-parsed JSON successfully: {self._json}"
                        )
                    else:
                        # If not pre-parsed, try parsing it
                        if parse_json(self.request_capsule) == 0:
                            result = get_json(self.request_capsule)
                            if result is not None:
                                self._json = result
                                print(
                                    f"[DEBUG-PY] JSON parsed successfully: {self._json}"
                                )
                            else:
                                print("[DEBUG-PY] JSON parsing returned None")
                                self._json = {}
                        else:
                            print("[DEBUG-PY] Failed to parse JSON in C")
                            self._json = {}
                else:
                    print("[DEBUG-PY] Not JSON content type")
                    self._json = {}
            except Exception as e:
                print(f"[DEBUG-PY] JSON parsing error: {e}")
                self._json = {}
        return self._json

    def form(self) -> Dict[str, str]:
        """Parse body as form data"""
        if self._parsed_form is None:
            try:
                from catzilla._catzilla import get_form_field, parse_form

                print(
                    f"[DEBUG-PY] Attempting to parse form data with content type: {self.content_type}"
                )
                if self.content_type == "application/x-www-form-urlencoded":
                    self._parsed_form = {}
                    # Try to get form fields from already parsed data
                    if self.body:
                        for pair in self.body.split("&"):
                            if "=" in pair:
                                key, _ = pair.split("=", 1)
                                # Get the value from C, it will be already URL-decoded
                                value = get_form_field(self.request_capsule, key)
                                if value is not None:
                                    print(f"[DEBUG-PY] Got form field: {key}={value}")
                                    self._parsed_form[key] = value
                                else:
                                    print(
                                        f"[DEBUG-PY] No value found for form field: {key}"
                                    )

                        if not self._parsed_form:
                            print("[DEBUG-PY] No form fields found, trying to parse")
                            # If we couldn't get any fields, try parsing
                            if parse_form(self.request_capsule) == 0:
                                # Try getting fields again after parsing
                                for pair in self.body.split("&"):
                                    if "=" in pair:
                                        key, _ = pair.split("=", 1)
                                        value = get_form_field(
                                            self.request_capsule, key
                                        )
                                        if value is not None:
                                            print(
                                                f"[DEBUG-PY] Got form field after parsing: {key}={value}"
                                            )
                                            self._parsed_form[key] = value
                            else:
                                print("[DEBUG-PY] Failed to parse form data in C")
                else:
                    print("[DEBUG-PY] Not form content type")
                    self._parsed_form = {}
            except Exception as e:
                print(f"[DEBUG-PY] Form parsing error: {e}")
                self._parsed_form = {}
        return self._parsed_form

    def text(self) -> str:
        """Get raw body as text"""
        if self._text is None:
            self._text = self.body or ""
        return self._text

    @property
    def client_ip(self) -> str:
        """Get the client's IP address"""
        if self._client_ip is not None:
            return self._client_ip

        # Try X-Forwarded-For header first
        forwarded_for = self.headers.get("x-forwarded-for")
        if forwarded_for:
            self._client_ip = forwarded_for.split(",")[0].strip()
            return self._client_ip

        # Try X-Real-IP header next
        real_ip = self.headers.get("x-real-ip")
        if real_ip:
            self._client_ip = real_ip
            return self._client_ip

        # Finally get it from the client object (implementation in C)
        from catzilla._catzilla import get_client_ip

        self._client_ip = get_client_ip(self.client) or "0.0.0.0"
        return self._client_ip

    @property
    def content_type(self) -> str:
        """Get normalized Content-Type header without parameters"""
        if self._content_type is None:
            from catzilla._catzilla import get_content_type

            self._content_type = get_content_type(self.request_capsule) or ""
            print(f"[DEBUG-PY] Got content type from C: {self._content_type}")

            # If we got an empty content type but have a Content-Type header, use that
            if not self._content_type and "content-type" in self.headers:
                header_value = self.headers["content-type"].split(";")[0].strip()
                print(f"[DEBUG-PY] Using content type from header: {header_value}")
                self._content_type = header_value

        return self._content_type


class Response:
    """Base HTTP Response class"""

    def __init__(
        self, status_code: int = 200, content_type: str = "text/plain", body: str = ""
    ):
        self.status_code = status_code
        self.content_type = content_type
        self.body = body

    def send(self, client):
        """Send the response using the C extension"""
        from catzilla._catzilla import send_response

        send_response(client, self.status_code, self.content_type, self.body)


class JSONResponse(Response):
    """HTTP Response with JSON body"""

    def __init__(self, data: Any, status_code: int = 200):
        super().__init__(status_code, "application/json", json.dumps(data))


class HTMLResponse(Response):
    """HTTP Response with HTML body"""

    def __init__(self, html: str, status_code: int = 200):
        super().__init__(status_code, "text/html", html)


# Type definition for route handlers
RouteHandler = Callable[[Request], Response]
