from __future__ import annotations

import secrets
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.services.intrusion_service import intrusion_service


class SecurityMiddleware(BaseHTTPMiddleware):
    """1, 4, 5, 8-bosqich: sarlavhalar, rate limit, IP blok, body limit."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._client_ip(request)
        request.state.client_ip = client_ip
        request.state.request_id = secrets.token_hex(8)

        blocked, reason = intrusion_service.is_blocked(client_ip)
        if blocked:
            return JSONResponse(
                status_code=403,
                content={"detail": "Kirish vaqtincha bloklangan", "reason": reason},
                headers=self._security_headers(),
            )

        if request.method != "OPTIONS":
            limit = settings.security_rate_limit_per_minute
            if request.url.path.endswith("/admin/login"):
                limit = settings.security_login_rate_limit_per_minute
            if not intrusion_service.check_rate_limit(client_ip, limit, window_sec=60):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Juda ko'p so'rov. Keyinroq urinib ko'ring."},
                    headers=self._security_headers(),
                )

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.security_max_body_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "So'rov hajmi ruxsat etilgan limitdan katta"},
                headers=self._security_headers(),
            )

        if settings.security_admin_ip_allowlist:
            if request.url.path.startswith(f"{settings.api_prefix}/admin") and client_ip not in settings.security_admin_ip_allowlist:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Admin panel bu IP dan ochilmaydi"},
                    headers=self._security_headers(),
                )

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        for key, value in self._security_headers().items():
            response.headers[key] = value
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        response.headers["X-Security-Environment"] = settings.security_environment
        return response

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    @staticmethod
    def _security_headers() -> dict[str, str]:
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; base-uri 'self'",
            "Cache-Control": "no-store",
        }
        if settings.security_environment == "production":
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return headers


def get_client_ip(request: Request) -> str:
    return getattr(request.state, "client_ip", "unknown")
