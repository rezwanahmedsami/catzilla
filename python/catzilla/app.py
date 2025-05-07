from typing import Callable, Any
from pydantic import BaseModel
from ._native import Router

class Catzilla:
    def __init__(self):
        self._router = Router()
        
    def get(self, path: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._router.add_route("GET", path, func)
            return func
        return decorator
    
    # Similar post(), put(), etc.