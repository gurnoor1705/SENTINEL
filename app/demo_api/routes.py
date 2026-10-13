
import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/demo", tags=["Demo API"])

PRODUCTS = {
    1: {"id": 1, "name": "Keyboard", "price": 1499},
    2: {"id": 2, "name": "Mouse", "price": 799},
    3: {"id": 3, "name": "Monitor", "price": 12999},
}

# In-memory fault state for the local demo service.
FAULT_STATE = {
    "type": "none",
    "delay_seconds": 0.0,
}


@router.get("/products")
async def list_products():
    # Simulate latency when enabled.
    if FAULT_STATE["type"] == "latency":
        await asyncio.sleep(FAULT_STATE["delay_seconds"])

    # Simulate temporary service unavailability.
    if FAULT_STATE["type"] == "http_503":
        raise HTTPException(
            status_code=503,
            detail="Injected fault: service temporarily unavailable",
        )

    return {
        "count": len(PRODUCTS),
        "products": list(PRODUCTS.values()),
    }


@router.get("/products/{product_id}")
async def get_product(product_id: int):
    product = PRODUCTS.get(product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail=f"Product {product_id} not found",
        )

    return product


@router.post("/faults/latency")
async def enable_latency(
    delay_seconds: float = Query(default=1.0, ge=0.1, le=3.0),
):
    FAULT_STATE["type"] = "latency"
    FAULT_STATE["delay_seconds"] = delay_seconds

    return {
        "message": "Latency fault enabled",
        "delay_seconds": delay_seconds,
    }


@router.post("/faults/http-503")
async def enable_http_503():
    FAULT_STATE["type"] = "http_503"
    FAULT_STATE["delay_seconds"] = 0.0

    return {
        "message": "HTTP 503 fault enabled",
    }


@router.delete("/faults")
async def clear_faults():
    FAULT_STATE["type"] = "none"
    FAULT_STATE["delay_seconds"] = 0.0

    return {
        "message": "All faults cleared",
    }


@router.get("/faults")
async def get_fault_status():
    return {
        "type": FAULT_STATE["type"],
        "delay_seconds": FAULT_STATE["delay_seconds"],
    }
