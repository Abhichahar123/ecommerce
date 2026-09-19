import httpx
import os
from fastapi import Request, HTTPException
from fastapi.responses import Response
from dotenv import load_dotenv

load_dotenv()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:8002")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8003")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://127.0.0.1:8004")


def get_target_url(path: str) -> str:
    """
    Path dekho aur sahi service ka URL return karo.
    
    /api/auth/*     → Auth Service
    /api/products/* → Product Service
    /api/orders/*   → Order Service
    /api/payments/* → Payment Service
    """
    if path.startswith("/api/auth"):
        # /api/auth/login → /auth/login
        service_path = path.replace("/api/auth", "/auth", 1)
        return f"{AUTH_SERVICE_URL}{service_path}"

    elif path.startswith("/api/products"):
        # /api/products/ → /products/
        service_path = path.replace("/api/products", "/products", 1)
        return f"{PRODUCT_SERVICE_URL}{service_path}"

    elif path.startswith("/api/orders"):
        # /api/orders/ → /orders/
        service_path = path.replace("/api/orders", "/orders", 1)
        return f"{ORDER_SERVICE_URL}{service_path}"

    elif path.startswith("/api/payments"):
        # /api/payments/ → /payments/
        service_path = path.replace("/api/payments", "/payments", 1)
        return f"{PAYMENT_SERVICE_URL}{service_path}"

    else:
        return None


async def forward_request(request: Request, target_url: str) -> Response:
    """
    Request ko target service pe forward karo.
    
    Kya forward hota hai:
    - HTTP method (GET, POST, PUT, DELETE)
    - Headers (Authorization token bhi)
    - Request body (JSON data)
    - Query parameters (?page=1&limit=10)
    """
    # Request body lo
    body = await request.body()

    # Headers forward karo — Authorization header zaroori hai
    headers = dict(request.headers)

    # Host header hata do — target service ka host alag hai
    headers.pop("host", None)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params)
            )

        # Service ka response wapas client ko bhejo
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable — target service is down"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Gateway timeout — service took too long to respond"
        )