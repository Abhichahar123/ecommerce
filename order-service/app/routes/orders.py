from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import os

from ..database import get_db
from ..models import Order, OrderStatus
from ..schemas import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:8002")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")


def verify_token(token: str) -> dict:
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{AUTH_SERVICE_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")


def get_product(product_id: int) -> dict:
    try:
        with httpx.Client() as client:
            response = client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Product not found")
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Product service unavailable")


def update_product_stock(product_id: int, new_stock: int):
    try:
        with httpx.Client() as client:
            response = client.put(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}",
                json={"stock": new_stock}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to update stock")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Product service unavailable")


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    # Step 1: Token verify karo
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.split(" ")[1]
    user_info = verify_token(token)
    user_id = user_info["id"]

    # Step 2: Product info lo
    product = get_product(order_data.product_id)

    # Step 3: Stock check karo
    current_stock = product["stock"]
    if current_stock < order_data.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {current_stock}, Requested: {order_data.quantity}"
        )

    # Step 4: Total price calculate karo
    total_price = product["price"] * order_data.quantity

    # Step 5: Order save karo
    new_order = Order(
        user_id=user_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        total_price=total_price,
        status=OrderStatus.confirmed.value
    )
    db.add(new_order)

    # Step 6: Stock update karo Product Service mein
    new_stock = current_stock - order_data.quantity
    update_product_stock(order_data.product_id, new_stock)

    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")

    token = authorization.split(" ")[1]
    user_info = verify_token(token)

    orders = db.query(Order).filter(
        Order.user_id == user_info["id"]
    ).all()

    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")

    token = authorization.split(" ")[1]
    user_info = verify_token(token)

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_info["id"]
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order