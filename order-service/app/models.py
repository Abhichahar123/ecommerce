from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from .database import Base
import enum


# Order ke possible statuses
class OrderStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(
        String,
        default=OrderStatus.pending.value
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())