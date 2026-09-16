import os
from pathlib import Path

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class PathTraversalError(Exception):
    """Raised when a resolved path is outside the allowed base directory."""
    pass


def safe_resolve_path(base_dir: Path, requested_path: str | Path) -> Path:
    """Resolve a path and ensure it remains strictly within the base_dir."""
    try:
        # Resolve to absolute paths, resolving symlinks and '..'
        resolved_base = base_dir.resolve(strict=False)
        resolved_requested = (resolved_base / Path(requested_path)).resolve(strict=False)
        
        # Check if the requested path is relative to the base path
        if not str(resolved_requested).startswith(str(resolved_base)):
            raise PathTraversalError("Path traversal attempt detected")
            
        return resolved_requested
    except Exception as exc:
        raise PathTraversalError(f"Invalid path: {exc}") from exc


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce a maximum payload size for incoming requests."""
    
    def __init__(self, app, max_upload_size: int = 100 * 1024 * 1024):
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_upload_size:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Payload too large. Maximum size is 100MB."},
                    )
            except ValueError:
                pass  # Malformed header; let FastAPI handle or reject later
        return await call_next(request)
