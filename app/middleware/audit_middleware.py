"""
Audit Middleware
=================
ASGI middleware that logs every HTTP request/response for audit trail.
"""

import time
import json
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database import SessionLocal
from app.models.audit import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Records method, path, client IP, status code, and response time
    for every request into the audit_logs table.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate response time
        process_time_ms = round((time.time() - start_time) * 1000, 2)

        # Extract client IP
        client_ip = request.client.host if request.client else "unknown"

        # Extract user ID from state if auth middleware set it
        user_id = getattr(request.state, "user_id", None) if hasattr(request, "state") else None

        # Log to database (fire-and-forget, non-blocking)
        try:
            db = SessionLocal()
            entry = AuditLog(
                user_id=user_id,
                action="http.request",
                resource_type="endpoint",
                resource_id=f"{request.method} {request.url.path}",
                details=json.dumps({
                    "method": request.method,
                    "path": str(request.url.path),
                    "query": str(request.url.query) if request.url.query else None,
                    "status_code": response.status_code,
                    "response_time_ms": process_time_ms,
                }),
                ip_address=client_ip,
            )
            db.add(entry)
            db.commit()
            db.close()
        except Exception:
            # Never let audit logging break the request
            pass

        # Add timing header
        response.headers["X-Process-Time-Ms"] = str(process_time_ms)

        return response
