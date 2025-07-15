# mcp.py

from functools import wraps
from typing import Callable, Optional

def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator to mark a function as an MCP tool.
    Can optionally attach metadata for registration.

    Usage:
        @tool()
        def my_tool(...): ...

        or

        @tool(name="custom_name", description="Does something")
        def my_tool(...): ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Attach optional metadata
        wrapper._tool_name = name or func.__name__
        wrapper._tool_description = description or func.__doc__

        return wrapper

    return decorator
