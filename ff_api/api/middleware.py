import time
import uuid
import asyncio
from typing import Dict, Tuple, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ff_api.api.errors import FFError, ERROR_HTTP_MAP, ErrorCode
from ff_api.api.schemas import PlayerResponse, ResponseMetadata, ErrorDetail
from ff_api.config.settings import settings

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rpm: int):
        super().__init__(app)
        self.rpm = rpm
        self._visits: Dict[str, List[float]] = {}
        self._prune_task = asyncio.create_task(self._periodic_prune())

    async def _periodic_prune(self):
        """Periodically remove IPs that haven't visited in over a minute to prevent memory leak."""
        while True:
            await asyncio.sleep(60)
            now = time.time()
            dead_ips = []
            for ip, visits in self._visits.items():
                # If the latest visit is older than 60s, the entire IP entry can be removed
                if not visits or visits[-1] < now - 60:
                    dead_ips.append(ip)
            for ip in dead_ips:
                del self._visits[ip]

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        visits = self._visits.get(client_ip, [])
        # Prune old visits for this specific IP
        visits = [v for v in visits if v > now - 60]

        if len(visits) >= self.rpm:
            return JSONResponse(
                status_code=429,
                content={
                    "metadata": {
                        "request_uid": request.query_params.get("uid", ""),
                        "request_region": request.query_params.get("region", ""),
                        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "response_time_ms": 0,
                        "api_version": settings.OB_VERSION,
                        "cache_hit": False
                    },
                    "data": None,
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Rate limit of {self.rpm} RPM exceeded",
                        "retryable": True,
                        "extra": {"retry_after": 60}
                    }
                },
                headers={"Retry-After": "60"}
            )

        visits.append(now)
        self._visits[client_ip] = visits
        return await call_next(request)

async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        if isinstance(exc, FFError):
            error = exc
        else:
            error = FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Internal server error: {str(exc)}")

        status_code = ERROR_HTTP_MAP.get(error.code, 500)

        return JSONResponse(
            status_code=status_code,
            content=PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=request.query_params.get("uid", "unknown"),
                    request_region=request.query_params.get("region", "unknown"),
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    response_time_ms=0,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                data=None,
                error=ErrorDetail(
                    code=error.code,
                    message=error.message,
                    retryable=error.retryable,
                    extra=error.extra
                )
            ).model_dump()
        )
