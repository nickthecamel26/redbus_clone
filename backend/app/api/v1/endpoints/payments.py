"""Payment endpoints for Razorpay integration."""

import os
import json
import razorpay
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from typing import List

from app.db.session import get_db
from app.models.booking import Booking, BookingStatus
from app.models.seat import Seat
from app.models.user import User
from app.schemas.payment import PaymentOrderCreate, PaymentOrderResponse, PaymentWebhook
from app.core.security import get_current_user
from app.core.logger import logger
from app.core.config import settings
from app.tasks import release_unpaid_seats, silence_cleanup

router = APIRouter()

# Initialize Razorpay client using settings
try:
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    # Initialize Utility instance for webhook signature verification
    razorpay_utility = razorpay.Utility(client)
except Exception as e:
    logger.error(f"Error initializing Razorpay client: {e}")
    raise HTTPException(status_code=500, detail="Failed to initialize Razorpay client")

@router.post("/create-order/{booking_id}", response_model=PaymentOrderResponse)
def create_payment_order(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a Razorpay order for the given booking."""
    try:
        logger.info(f"Creating payment order for booking {booking_id} by user {current_user.id}")
        
        # Fetch booking with trip and seat details
        booking = (
            db.query(Booking)
            .options(joinedload(Booking.trip), joinedload(Booking.seat))
            .filter(Booking.id == booking_id)
            .first()
        )
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Verify ownership
        if booking.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only create orders for your own bookings")
        
        # Check if already paid
        if booking.status == BookingStatus.CONFIRMED:
            raise HTTPException(status_code=400, detail="Booking is already confirmed")
        
        # Check if cancelled
        if booking.status == BookingStatus.CANCELLED:
            raise HTTPException(status_code=400, detail="Cannot create order for cancelled booking")
        
        # Convert amount to paise (Razorpay expects amount in smallest currency unit)
        amount_in_paise = int(float(booking.total_price) * 100)
        
        # Create Razorpay order with proper error handling
        try:
            razorpay_order = client.order.create({
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"booking_{booking_id}",
                "notes": {
                    "booking_id": booking_id,
                    "user_id": current_user.id
                }
            })
            
            logger.info(f"Created Razorpay order {razorpay_order['id']} for booking {booking_id}")
            
            return PaymentOrderResponse(
                razorpay_order_id=razorpay_order["id"],
                amount=amount_in_paise,
                currency=razorpay_order["currency"],
                booking_id=booking_id,
                status=razorpay_order["status"]
            )
        except Exception as razorpay_error:
            logger.error(f"Razorpay API error for booking {booking_id}: {razorpay_error}")
            raise HTTPException(status_code=500, detail=f"Payment gateway error: {str(razorpay_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment order for booking {booking_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")

@router.post("/mock-webhook")
def mock_payment_webhook(webhook_data: PaymentWebhook, db: Session = Depends(get_db)):
    """Mock webhook endpoint to simulate successful payment."""
    try:
        logger.info(f"Mock webhook received for booking {webhook_data.booking_id}, order {webhook_data.razorpay_order_id}")
        
        # Fetch booking with seat details
        booking = (
            db.query(Booking)
            .options(joinedload(Booking.seat))
            .filter(Booking.id == webhook_data.booking_id)
            .first()
        )
        
        if not booking:
            logger.error(f"Booking {webhook_data.booking_id} not found in webhook")
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking.status == BookingStatus.CONFIRMED:
            logger.info(f"Booking {webhook_data.booking_id} already confirmed")
            return {"status": "already_processed", "message": "Booking already confirmed"}
        
        # Atomic transaction: Update booking status and ensure seat availability
        try:
            # Update booking status to CONFIRMED
            booking.status = BookingStatus.CONFIRMED
            
            # Ensure seat is marked as unavailable (double-check)
            if booking.seat:
                booking.seat.is_available = False
                logger.info(f"Ensured seat {booking.seat.id} ({booking.seat.seat_number}) is unavailable")
            
            db.commit()
            logger.info(f"Payment webhook: Booking {webhook_data.booking_id} confirmed successfully")
            
            # Trigger Celery task to silence cleanup for this booking
            silence_cleanup.delay(webhook_data.booking_id)
            logger.info(f"Triggered silence_cleanup task for booking {webhook_data.booking_id}")
            
            return {
                "status": "success",
                "message": f"Booking {webhook_data.booking_id} confirmed",
                "booking_id": webhook_data.booking_id,
                "razorpay_payment_id": webhook_data.razorpay_payment_id
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed in webhook for booking {webhook_data.booking_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to confirm booking")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mock webhook for booking {webhook_data.booking_id}: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


def process_webhook_payment(booking_id: int):
    """Background task to process payment confirmation."""
    db = next(get_db())
    try:
        logger.info(f"[Background Task] Processing payment for booking {booking_id}")
        
        # Fetch booking with seat details
        booking = (
            db.query(Booking)
            .options(joinedload(Booking.seat))
            .filter(Booking.id == booking_id)
            .first()
        )
        
        if not booking:
            logger.error(f"[Background Task] Booking {booking_id} not found")
            return
        
        if booking.status == BookingStatus.CONFIRMED:
            logger.info(f"[Background Task] Booking {booking_id} already confirmed")
            return
        
        # Atomic transaction: Update booking status and ensure seat availability
        try:
            booking.status = BookingStatus.CONFIRMED
            
            if booking.seat:
                booking.seat.is_available = False
                logger.info(f"[Background Task] Seat {booking.seat.id} marked as unavailable")
            
            db.commit()
            logger.info(f"[Background Task] Booking {booking_id} confirmed successfully")
            
            # Trigger Celery task to silence cleanup
            silence_cleanup.delay(booking_id)
            logger.info(f"[Background Task] Triggered silence_cleanup for booking {booking_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"[Background Task] Transaction failed for booking {booking_id}: {e}")
    finally:
        db.close()


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Secure Razorpay webhook endpoint with signature verification."""
    try:
        # Get raw body and signature
        raw_body = await request.body()
        signature = request.headers.get("X-Razorpay-Signature")
        
        logger.info("Received Razorpay webhook request")
        
        if not signature:
            logger.error("Missing X-Razorpay-Signature header")
            raise HTTPException(status_code=400, detail="Missing signature header")
        
        # Verify webhook signature
        try:
            razorpay_utility.verify_webhook_signature(
                raw_body.decode("utf-8"),
                signature,
                settings.RAZORPAY_WEBHOOK_SECRET
            )
            logger.info("Webhook Signature Verified")
        except Exception as e:
            logger.error(f"Invalid Signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse webhook payload
        payload = json.loads(raw_body)
        event = payload.get("event")
        
        logger.info(f"Webhook event received: {event}")
        
        # Handle payment events
        if event in ["payment.captured", "order.paid"]:
            # Extract booking_id from notes or payload
            if event == "payment.captured":
                notes = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("notes", {})
                booking_id = notes.get("booking_id")
            else:  # order.paid
                notes = payload.get("payload", {}).get("order", {}).get("entity", {}).get("notes", {})
                booking_id = notes.get("booking_id")
            
            if booking_id:
                logger.info(f"Processing {event} for booking {booking_id}")
                # Use background task for database operations
                background_tasks.add_task(process_webhook_payment, booking_id)
            else:
                logger.warning(f"No booking_id found in {event} webhook payload")
        else:
            logger.info(f"Ignoring webhook event: {event}")
        
        # Return 200 OK immediately to Razorpay
        return {"status": "received", "event": event}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Still return 200 to prevent Razorpay retries for unexpected errors
        return {"status": "error", "message": str(e)}
