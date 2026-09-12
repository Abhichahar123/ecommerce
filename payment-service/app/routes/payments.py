from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import os
import random

from ..database import get_db
from ..models import Payment
from ..schemas import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")


# ─── Helper Functions ────────────────────────────────────

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


def process_mock_payment(amount: float) -> tuple:
    """
    Mock payment processor
    Real world mein yahan Razorpay/Stripe API call hoti
    
    Returns: (status, failure_reason)
    90% success, 10% failure
    """
    # Random number 1-10 generate karo
    roll = random.randint(1, 10)

    if roll <= 9:
        # 90% chance success
        return "success", None
    else:
        # 10% chance failure
        failure_reasons = [
            "Insufficient funds",
            "Card declined",
            "Bank server error",
            "Transaction limit exceeded"
        ]
        reason = random.choice(failure_reasons)
        return "failed", reason


# ─── Endpoints ───────────────────────────────────────────

@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Payment process karo — idempotency ke saath"""

    # Step 1: Token verify karo
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )
    token = authorization.split(" ")[1]
    user_info = verify_token(token)
    user_id = user_info["id"]

    # Step 2: Idempotency check — sabse important step
    existing_payment = db.query(Payment).filter(
        Payment.idempotency_key == payment_data.idempotency_key
    ).first()

    if existing_payment:
        # Yeh payment pehle process ho chuki hai
        # Dobara process mat karo — same result return karo
        print(f"✓ Idempotency hit: {payment_data.idempotency_key} already processed")
        return existing_payment

    # Step 3: Mock payment process karo
    status, failure_reason = process_mock_payment(payment_data.amount)

    print(f"Payment status: {status}")
    if failure_reason:
        print(f"Failure reason: {failure_reason}")

    # Step 4: Payment database mein save karo
    new_payment = Payment(
        order_id=payment_data.order_id,
        user_id=user_id,
        amount=payment_data.amount,
        status=status,
        idempotency_key=payment_data.idempotency_key,
        failure_reason=failure_reason
    )

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return new_payment


@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Apni saari payments dekho"""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")

    token = authorization.split(" ")[1]
    user_info = verify_token(token)

    payments = db.query(Payment).filter(
        Payment.user_id == user_info["id"]
    ).all()

    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Ek payment ki detail dekho"""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")

    token = authorization.split(" ")[1]
    user_info = verify_token(token)

    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == user_info["id"]
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return payment