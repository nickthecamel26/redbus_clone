"""Payment schemas for Razorpay integration."""

from pydantic import BaseModel
from typing import Optional

class PaymentOrderCreate(BaseModel):
    """Request to create a payment order."""
    booking_id: int

class PaymentOrderResponse(BaseModel):
    """Response containing Razorpay order details."""
    razorpay_order_id: str
    amount: int
    currency: str
    booking_id: int
    status: str

class PaymentWebhook(BaseModel):
    """Mock webhook payload for payment simulation."""
    razorpay_order_id: str
    razorpay_payment_id: str
    status: str
    booking_id: int
