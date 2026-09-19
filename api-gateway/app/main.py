from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .rate_limiter import check_rate_limit
from .router import get_target_url, forward_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✓ API Gateway starting...")
    yield
    print("✓ API Gateway shutting down...")


app = FastAPI(
    title="API Gateway",
    description="Single entry point for all microservices"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "API Gateway is running",
        "services": {
            "auth": "/api/auth/*",
            "products": "/api/products/*",
            "orders": "/api/orders/*",
            "payments": "/api/payments/*"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "api-gateway"}


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def gateway(
    path: str,
    request: Request,
    _=Depends(check_rate_limit)  # Rate limiting har request pe
):
    """
    Main gateway endpoint.
    
    Har request yahan aati hai:
    1. Rate limit check hoti hai (Depends)
    2. Target URL nikala jaata hai
    3. Request forward hoti hai
    4. Response wapas bheja jaata hai
    """

    # Full path banao
    full_path = f"/api/{path}"

    # Query string bhi add karo agar hai
    if request.query_params:
        full_path = f"{full_path}?{request.query_params}"

    # Target service URL nikalo
    target_url = get_target_url(f"/api/{path}")

    if not target_url:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Route not found",
                "message": f"No service found for path: /api/{path}",
                "available_routes": [
                    "/api/auth/*",
                    "/api/products/*",
                    "/api/orders/*",
                    "/api/payments/*"
                ]
            }
        )

    # Request forward karo
    return await forward_request(request, target_url)