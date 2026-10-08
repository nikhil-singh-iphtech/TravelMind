from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from app.db.session import Base


class Booking(Base):
    """
    Persisted record of a user's trip booking attempt.
    Status states: pending | confirmed | price_changed | failed | cancelled
    """
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(
        String, unique=True, index=True, default=lambda: f"TM-BKG-{uuid.uuid4().hex[:6].upper()}"
    )
    run_id = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")  # pending | confirmed | price_changed | failed | cancelled
    flight_id = Column(String, nullable=True)
    hotel_id = Column(String, nullable=True)
    quoted_price = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
