"""
Type definitions for Catzilla
"""

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class Request:
    """HTTP Request object"""

    method: str
    path: str
    body: str
    client: Any  # The client capsule from C
    headers: Dict[str, str] = None
    query_params: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.query_params is None:
            self.query_params = {}

    @property
    def json(self) -> Any:
        """Parse body as JSON"""
        if not self.body:
            return {}
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return {}


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
