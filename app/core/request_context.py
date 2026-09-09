from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.core.logging import get_logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request context and structured HTTP logs to every API request."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        clear_contextvars()

        request_id = request.headers.get("X-Request-ID") or str(uuid4())

        bind_contextvars(
            request_id=request_id,
        )

        logger = get_logger("http").bind(
            method=request.method,
            path=request.url.path,
        )

        started_at = perf_counter()

        logger.info("http_request_started")

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            logger.exception(
                "http_request_failed",
                duration_ms=duration_ms,
            )

            clear_contextvars()
            raise

        duration_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "http_request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        clear_contextvars()

        return response
