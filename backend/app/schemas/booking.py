from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel


class CreateBookingRequest(BaseModel):
    run_id: str
    flight_id: str | None = None
    hotel_id: str | None = None
    quoted_price: Decimal
    currency: str = "INR"
    idempotency_key: str
    accept_price_change: bool = False


class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    run_id: str
    user_id: int
    status: Literal["pending", "confirmed", "price_changed", "failed", "cancelled"]
    flight_id: str | None = None
    hotel_id: str | None = None
    quoted_price: Decimal
    final_price: Decimal
    currency: str
    idempotency_key: str
    created_at: datetime
    message: str | None = None
