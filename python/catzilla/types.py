"""
Type definitions for Catzilla
"""

import json
from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import parse_qs

from .ui import log_types_debug, log_types_error


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
    _path_params: Dict[str, str] = None  # Internal storage for path params
    _client_ip: Optional[str] = None
    _parsed_form: Optional[Dict[str, str]] = None
    _text: Optional[str] = None
    _json: Optional[Any] = None
    _content_type: Optional[str] = None
    _files: Optional[Dict[str, Any]] = None
    _loaded_query_params: bool = False

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self._query_params is None:
            self._query_params = {}
        if self._path_params is None:
            self._path_params = {}

        # Normalize header keys to lowercase for consistent access
        self.headers = {k.lower(): v for k, v in self.headers.items()}

    @property
    def path_params(self) -> Dict[str, str]:
        """Get path parameters extracted from the URL"""
        return self._path_params

    @path_params.setter
    def path_params(self, value: Dict[str, str]):
        """Set path parameters"""
        self._path_params = value or {}

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
                                log_types_debug(
                                    "Got query param from C: %s=%s", key, value
                                )
                                self._query_params[key] = value
                self._loaded_query_params = True
            except Exception as e:
                log_types_error("Error loading query params from C: %s", e)
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

                log_types_debug(
                    "Attempting to parse JSON with content type: %s", self.content_type
                )
                if self.content_type == "application/json":
                    # Try to get the JSON directly first, since it might be pre-parsed
                    result = get_json(self.request_capsule)
                    if result is not None:
                        self._json = result
                        log_types_debug(
                            "Got pre-parsed JSON successfully: %s", self._json
                        )
                    else:
                        # If not pre-parsed, try parsing it
                        if parse_json(self.request_capsule) == 0:
                            result = get_json(self.request_capsule)
                            if result is not None:
                                self._json = result
                                log_types_debug(
                                    "JSON parsed successfully: %s", self._json
                                )
                            else:
                                log_types_debug("JSON parsing returned None")
                                self._json = {}
                        else:
                            log_types_debug("Failed to parse JSON in C")
                            self._json = {}
                else:
                    log_types_debug("Not JSON content type")
                    self._json = {}
            except Exception as e:
                log_types_error("JSON parsing error: %s", e)
                self._json = {}
        return self._json

    def form(self) -> Dict[str, str]:
        """Parse body as form data"""
        if self._parsed_form is None:
            try:
                from catzilla._catzilla import (
                    get_form_field,
                    multipart_parse,
                    parse_form,
                )

                log_types_debug(
                    "Attempting to parse form data with content type: %s",
                    self.content_type,
                )

                self._parsed_form = {}

                if self.content_type == "application/x-www-form-urlencoded":
                    # Handle URL-encoded form data
                    if self.body:
                        for pair in self.body.split("&"):
                            if "=" in pair:
                                key, _ = pair.split("=", 1)
                                # Get the value from C, it will be already URL-decoded
                                value = get_form_field(self.request_capsule, key)
                                if value is not None:
                                    log_types_debug("Got form field: %s=%s", key, value)
                                    self._parsed_form[key] = value
                                else:
                                    log_types_debug(
                                        "No value found for form field: %s", key
                                    )

                        if not self._parsed_form:
                            log_types_debug("No form fields found, trying to parse")
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
                                            log_types_debug(
                                                "Got form field after parsing: %s=%s",
                                                key,
                                                value,
                                            )
                                            self._parsed_form[key] = value
                            else:
                                log_types_debug("Failed to parse form data in C")

                elif self.content_type and "multipart/form-data" in self.content_type:
                    # Handle multipart form data by extracting text fields from files
                    log_types_debug(
                        "Parsing multipart form data by extracting text fields from files"
                    )
                    try:
                        # Get files parsed by multipart parser
                        files = self.files  # Property, not method
                        log_types_debug("Got files dict: %s", files)
                        if files and isinstance(files, dict):
                            # Extract text fields (non-file uploads) from the files dict
                            for field_name, file_info in files.items():
                                log_types_debug(
                                    "Processing file: %s -> %s", field_name, file_info
                                )
                                if isinstance(file_info, dict):
                                    # Check if this is a text field (no real filename, small size)
                                    filename = file_info.get("filename", "")
                                    size = file_info.get("size", 0)
                                    content_type = file_info.get("content_type", "")
                                    content = file_info.get("content", "")

                                    log_types_debug(
                                        "Field %s: filename=%s, size=%d, content_type=%s, content_type=%s",
                                        field_name,
                                        filename,
                                        size,
                                        content_type,
                                        type(content),
                                    )

                                    # Text fields typically have filename="unknown" or empty, and reasonable size
                                    if (
                                        filename in ["unknown", "", None]
                                        and size < 1024
                                        and content_type  # Less than 1KB - likely text field
                                        in [
                                            "application/octet-stream",
                                            "text/plain",
                                            "",
                                        ]
                                    ):

                                        # Try to read the content as text
                                        if isinstance(content, bytes):
                                            content = content.decode(
                                                "utf-8", errors="ignore"
                                            )
                                        elif isinstance(content, str):
                                            pass  # Already a string
                                        else:
                                            content = str(content)

                                        self._parsed_form[field_name] = content
                                        log_types_debug(
                                            "Extracted text field from multipart: %s=%s",
                                            field_name,
                                            content,
                                        )

                            log_types_debug(
                                "Successfully extracted %d form fields from multipart data",
                                len(self._parsed_form),
                            )
                        else:
                            log_types_debug("No files found in multipart data")
                    except Exception as multipart_error:
                        log_types_error(
                            "Multipart form field extraction failed: %s",
                            multipart_error,
                        )
                        import traceback

                        log_types_error("Traceback: %s", traceback.format_exc())
                        # No fallback for multipart - it either works or doesn't
                else:
                    log_types_debug(
                        "Unsupported content type for form parsing: %s",
                        self.content_type,
                    )

            except Exception as e:
                log_types_error("Form parsing error: %s", e)
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

        # Finally try to get it from the client object (implementation in C)
        try:
            from catzilla._catzilla import get_client_ip

            if self.client:
                self._client_ip = get_client_ip(self.client)
                return self._client_ip
        except (ImportError, AttributeError):
            pass

        # Return None if we couldn't get the IP
        return None

    @property
    def content_type(self) -> str:
        """Get normalized Content-Type header without parameters"""
        if self._content_type is None:
            from catzilla._catzilla import get_content_type

            self._content_type = get_content_type(self.request_capsule) or ""
            log_types_debug("Got content type from C: %s", self._content_type)

            # If we got an empty content type but have a Content-Type header, use that
            if not self._content_type and "content-type" in self.headers:
                header_value = self.headers["content-type"].split(";")[0].strip()
                log_types_debug("Using content type from header: %s", header_value)
                self._content_type = header_value

        return self._content_type

    @property
    def files(self) -> Dict[str, Any]:
        """Get uploaded files from multipart/form-data requests"""
        if self._files is None:
            try:
                from catzilla._catzilla import get_files

                self._files = get_files(self.request_capsule) or {}
                log_types_debug("Got files from C: %s", list(self._files.keys()))
            except Exception as e:
                log_types_error("Error loading files from C: %s", e)
                self._files = {}
        return self._files

    def get_header(self, name: str) -> Optional[str]:
        """Get a request header by name using lazy loading from C"""
        try:
            from catzilla._catzilla import get_header

            # Only extract the specific header when requested
            header_value = get_header(self.request_capsule, name)
            log_types_debug("Got header from C: %s=%s", name, header_value)
            return header_value
        except Exception as e:
            log_types_error("Error getting header from C: %s", e)
            # Fallback to pre-loaded headers if available
            return self.headers.get(name.lower()) if self.headers else None

    @property
    def raw_headers(self) -> Dict[str, str]:
        """Get all request headers as a dictionary"""
        return {k.lower(): v for k, v in self.headers.items()}


class Response:
    """Base HTTP Response class"""

    def __init__(
        self,
        status_code: int = 200,
        content_type: str = "text/plain",
        body: str = "",
        headers: Optional[Dict[str, str]] = None,
    ):
        self.status_code = status_code
        self.content_type = content_type
        self.body = body
        self._headers = {}
        self._cookies = SimpleCookie()

        # Normalize and set headers
        if headers:
            for key, value in headers.items():
                self.set_header(key, value)

    def set_header(self, name: str, value: str) -> None:
        """Set a response header, normalizing the header name"""
        name = name.lower().strip()
        if name == "set-cookie":
            if name not in self._headers:
                self._headers[name] = []
            if isinstance(value, list):
                self._headers[name].extend(value)
            else:
                self._headers[name].append(value)
        else:
            self._headers[name] = str(value)

    def get_header(self, name: str) -> Optional[str]:
        """Get a response header by name"""
        name = name.lower().strip()
        header_value = self._headers.get(name)
        if header_value is not None:
            if isinstance(header_value, list):
                return header_value[0] if header_value else None
            return header_value
        return None

    def get_all_headers(self) -> List[str]:
        """Get all headers as a list of 'Name: Value' strings"""
        headers = []
        for name, value in self._headers.items():
            if name == "set-cookie":
                if isinstance(value, list):
                    for cookie in value:
                        headers.append(f"Set-Cookie: {cookie}")
            else:
                headers.append(f"{name}: {value}")
        return headers

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
    ) -> None:
        """Set a cookie with the given name and value."""
        self._cookies[name] = value
        morsel = self._cookies[name]

        if max_age is not None:
            morsel["max-age"] = max_age
        if expires is not None:
            morsel["expires"] = expires
        if path is not None:
            morsel["path"] = path
        if domain is not None:
            morsel["domain"] = domain
        if secure:
            morsel["secure"] = secure
        if httponly:
            morsel["httponly"] = httponly
        if samesite is not None:
            morsel["samesite"] = samesite

        # Add cookie to headers immediately
        cookie_str = morsel.output(header="").strip()
        self.set_header("Set-Cookie", cookie_str)

    def send(self, client):
        """Send the response using the C extension"""
        from catzilla._catzilla import send_response

        # Calculate body length in bytes for Content-Length header
        body_bytes = (
            self.body.encode("utf-8") if isinstance(self.body, str) else self.body
        )
        body_length = len(body_bytes) if body_bytes else 0

        # Build properly formatted headers including Content-Type and all custom headers
        headers = [
            f"Content-Type: {self.content_type}",
            f"Content-Length: {body_length}",
        ]

        # Add all custom headers
        for name, value in self._headers.items():
            if name == "set-cookie":
                if isinstance(value, list):
                    for cookie in value:
                        headers.append(f"Set-Cookie: {cookie}")
                else:
                    headers.append(f"Set-Cookie: {value}")
            elif name.lower() not in [
                "content-type",
                "content-length",
            ]:  # Avoid duplicates
                headers.append(f"{name.title()}: {value}")

        # Join headers with proper HTTP line endings
        headers_str = "\r\n".join(headers) + "\r\n" if headers else ""

        # Send response with formatted headers
        # Convert body to string for C interface
        body_str = (
            body_bytes.decode("utf-8") if isinstance(body_bytes, bytes) else self.body
        )
        send_response(client, self.status_code, headers_str, body_str)


class JSONResponse(Response):
    """HTTP Response with JSON body"""

    def __init__(
        self,
        data: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        # Create headers dict if not provided
        if headers is None:
            headers = {}

        # Ensure content type is set
        headers["Content-Type"] = "application/json"

        super().__init__(
            status_code=status_code,
            content_type="application/json",
            body=json.dumps(data),
            headers=headers,
        )


class HTMLResponse(Response):
    """HTTP Response with HTML body"""

    def __init__(
        self,
        html: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            status_code=status_code,
            content_type="text/html",
            body=html,
            headers=headers,
        )


# Type definition for route handlers
RouteHandler = Callable[[Request], Union[Response, str, dict]]
