import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from app.demo_api.routes import router as demo_router
from app.database import get_connection, initialize_database 
from fastapi import FastAPI, Request, Query

# Configure structured, readable application logs.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("sentinel")


app = FastAPI(
    title="SENTINEL",
    description="AI-powered software reliability platform",
    version="0.1.0",
)
initialize_database()

app.include_router(demo_router)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response

    except Exception:
        logger.exception(
            "Request failed | request_id=%s | method=%s | path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        raise

    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "HTTP request | request_id=%s | method=%s | path=%s "
            "| status_code=%s | duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )

        try:
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO request_logs
                    (request_id, method, path, status_code, duration_ms)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        request_id,
                        request.method,
                        request.url.path,
                        status_code,
                        duration_ms,
                    ),
                )
        except Exception:
            logger.exception(
                "Failed to save request log | request_id=%s",
                request_id,
            )


@app.get("/")
async def root():
    return {
        "service": "SENTINEL",
        "message": "Software reliability platform is running",
    }


@app.get("/health")
async def health(request: Request):
    return {
        "status": "healthy",
        "service": "SENTINEL",
        "request_id": request.state.request_id,
    }


@app.get("/monitoring/requests")
async def get_request_history(
    limit: int = Query(default=20, ge=1, le=100),
):
    """Return the most recent recorded API requests."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, request_id, method, path, status_code,
                   duration_ms, created_at
            FROM request_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return {
        "count": len(rows),
        "requests": [dict(row) for row in rows],
    }


@app.get("/monitoring/metrics")
async def get_reliability_metrics():
    """Calculate reliability metrics from recorded requests."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_requests,
                COALESCE(
                    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END),
                    0
                ) AS failed_requests,
                COALESCE(AVG(duration_ms), 0) AS avg_response_time_ms
            FROM request_logs
            """
        ).fetchone()

    total = row["total_requests"]
    failed = row["failed_requests"]

    failure_rate = (failed / total * 100) if total else 0.0

    return {
        "total_requests": total,
        "failed_requests": failed,
        "failure_rate_percent": round(failure_rate, 2),
        "avg_response_time_ms": round(
            row["avg_response_time_ms"], 2
        ),
    }
