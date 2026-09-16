import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

import structlog

def setup_logging() -> None:
    """Initialize structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logger = structlog.get_logger("api.request")
        start_time = time.time()
        
        response = None
        try:
            response = await call_next(request)
        finally:
            process_time = time.time() - start_time
            status_code = response.status_code if response else 500
            
            logger.info(
                "request_completed",
                method=request.method,
                url=str(request.url.path),
                status_code=status_code,
                process_time_ms=round(process_time * 1000, 2)
            )
        return response
