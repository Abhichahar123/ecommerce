from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import os
import redis
import time

from ..database import get_db
from ..models import Order, OrderStatus
from ..schemas import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:8002")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis connection — lock ke liye
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Lock kitni der tak valid rahega (milliseconds)
LOCK_EXPIRE_MS = 10000  # 10 seconds


# ─── Lock Helper Functions ───────────────────────────────

def acquire_lock(product_id: int) -> bool:
    """
    Redis mein product ke liye lock lo.
    
    NX = sirf tab set karo jab key exist na kare (atomic)
    PX = milliseconds mein expiry
    
    Return: True agar lock mili, False agar nahi mili
    """
    lock_key = f"lock:product:{product_id}"
    result = redis_client.set(lock_key, "locked", nx=True, px=LOCK_EXPIRE_MS)
    return result is not None


def release_lock(product_id: int):
    """Lock release karo — kaam khatam hone ke baad"""
    lock_key = f"lock:product:{product_id}"
    redis_client.delete(lock_key)


def acquire_lock_with_retry(product_id: int, max_retries: int = 3) -> bool:
    """
    Lock lene ki 3 baar koshish karo.
    
    Kyon retry? Agar pehli baar lock nahi mili —
    shayad doosra request abhi khatam ho raha ho.
    Thoda wait karo aur dobara try karo.
    """
    for attempt in range(max_retries):
        if acquire_lock(product_id):
            print(f"✓ Lock acquired for product {product_id} on attempt {attempt + 1}")
            return True

        print(f"✗ Lock attempt {attempt + 1} failed, retrying...")
        time.sleep(0.1)  # 100ms wait karo

    return False  # Teeno attempts fail ho gaye


# ─── Service Communication Functions ────────────────────

def verify_token(token: str) -> dict:
    """Auth Service se token verify karo"""
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
    """Product Service se product info lo"""
    try:
        with httpx.Client() as client:
            response = client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Product not found")
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Product service unavailable")


def update_product_stock(product_id: int, new_stock: int):
    """Product Service mein stock update karo"""
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


# ─── Endpoints ───────────────────────────────────────────

@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Order place karo — Redis distributed lock ke saath.
    
    Flow:
    1. Token verify karo
    2. Product check karo
    3. Redis lock lo (race condition prevent)
    4. Stock check karo (lock ke andar)
    5. Order save karo
    6. Stock update karo
    7. Lock release karo
    """

    # Step 1: Token verify karo
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )
    token = authorization.split(" ")[1]
    user_info = verify_token(token)
    user_id = user_info["id"]

    # Step 2: Product exist karta hai check karo
    product = get_product(order_data.product_id)

    # Step 3: Redis Lock Lo — CRITICAL SECTION SHURU
    lock_acquired = acquire_lock_with_retry(order_data.product_id)

    if not lock_acquired:
        raise HTTPException(
            status_code=409,  # 409 = Conflict
            detail="Product is currently being processed by another request. Please try again."
        )

    try:
        # Step 4: Lock ke andar fresh stock check karo
        # Kyon fresh? Lock lene mein time lag sakta hai
        # Us time mein stock change ho sakta tha
        fresh_product = get_product(order_data.product_id)
        current_stock = fresh_product["stock"]

        print(f"Product {order_data.product_id} stock: {current_stock}, requested: {order_data.quantity}")

        if current_stock < order_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {current_stock}, Requested: {order_data.quantity}"
            )

        # Step 5: Order save karo
        total_price = fresh_product["price"] * order_data.quantity

        new_order = Order(
            user_id=user_id,
            product_id=order_data.product_id,
            quantity=order_data.quantity,
            total_price=total_price,
            status=OrderStatus.confirmed.value
        )
        db.add(new_order)

        # Step 6: Stock update karo
        new_stock = current_stock - order_data.quantity
        update_product_stock(order_data.product_id, new_stock)

        db.commit()
        db.refresh(new_order)

        print(f"✓ Order {new_order.id} confirmed. New stock: {new_stock}")

        return new_order

    finally:
        # Step 7: Lock HAMESHA release karo
        # finally block guarantee karta hai —
        # chahe error aaye ya na aaye, lock release hogi
        release_lock(order_data.product_id)
        print(f"✓ Lock released for product {order_data.product_id}")


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Apne sab orders dekho"""
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
    """Ek order ki detail dekho"""
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