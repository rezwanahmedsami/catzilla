"""
Type definitions for Catzilla
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable


@dataclass
class Request:
    """HTTP Request object"""
    method: str
    path: str
    body: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    
    @property
    def json(self) -> Any:
        """Parse body as JSON"""
        if not self.body:
            return {}
        return json.loads(self.body)


class Response:
    """Base HTTP Response class"""
    def __init__(self, status_code: int, headers: Optional[Dict[str, str]] = None, body: Optional[str] = None):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body or ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to a dictionary"""
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
        }


class JSONResponse(Response):
    """HTTP Response with JSON body"""
    def __init__(self, data: Any, status_code: int = 200, headers: Optional[Dict[str, str]] = None):
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        super().__init__(status_code, headers, json.dumps(data))


class HTMLResponse(Response):
    """HTTP Response with HTML body"""
    def __init__(self, html: str, status_code: int = 200, headers: Optional[Dict[str, str]] = None):
        headers = headers or {}
        headers["Content-Type"] = "text/html"
        super().__init__(status_code, headers, html)


RouteHandler = Callable[[Request], Response]