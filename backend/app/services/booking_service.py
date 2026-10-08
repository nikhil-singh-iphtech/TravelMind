from decimal import Decimal
import logging
from sqlalchemy import select

from app.db.models.booking import Booking
from app.db.models.planning_run import PlanningRun
from app.db.session import SessionLocal
from app.providers.mock_booking_provider import MockBookingProvider
from app.schemas.booking import BookingResponse, CreateBookingRequest

logger = logging.getLogger(__name__)


class BookingService:
    """
    Handles trip booking creation, price revalidation, authorization, idempotency, and cancellation.
    """

    def __init__(self, provider: MockBookingProvider | None = None):
        self.provider = provider or MockBookingProvider()

    def create_booking(self, user_id: int, req: CreateBookingRequest) -> BookingResponse:
        with SessionLocal() as session:
            # 1. Idempotency Check
            existing = session.execute(
                select(Booking).where(Booking.idempotency_key == req.idempotency_key)
            ).scalar_one_or_none()

            if existing:
                if existing.user_id != user_id:
                    raise PermissionError("Access denied for idempotency key")
                return self._to_response(existing, message="Existing booking retrieved via idempotency key")

            # 2. Authorization Check (Verify run ownership)
            run = session.execute(
                select(PlanningRun).where(PlanningRun.run_id == req.run_id, PlanningRun.user_id == user_id)
            ).scalar_one_or_none()

            if not run:
                raise ValueError("Travel plan not found or access denied")

            # 3. Revalidate with provider
            import asyncio
            provider_res = asyncio.run(
                self.provider.revalidate_and_reserve(req.flight_id, req.hotel_id, req.quoted_price)
            )

            if not provider_res.available:
                booking = Booking(
                    run_id=req.run_id,
                    user_id=user_id,
                    status="failed",
                    flight_id=req.flight_id,
                    hotel_id=req.hotel_id,
                    quoted_price=float(req.quoted_price),
                    final_price=float(req.quoted_price),
                    currency=req.currency,
                    idempotency_key=req.idempotency_key,
                )
                session.add(booking)
                session.commit()
                session.refresh(booking)
                return self._to_response(booking, message=provider_res.error_message or "Selected offer unavailable")

            revalidated_price = provider_res.revalidated_price

            # Check if price changed
            if revalidated_price > req.quoted_price and not req.accept_price_change:
                booking = Booking(
                    run_id=req.run_id,
                    user_id=user_id,
                    status="price_changed",
                    flight_id=req.flight_id,
                    hotel_id=req.hotel_id,
                    quoted_price=float(req.quoted_price),
                    final_price=float(revalidated_price),
                    currency=req.currency,
                    idempotency_key=req.idempotency_key,
                )
                session.add(booking)
                session.commit()
                session.refresh(booking)
                return self._to_response(
                    booking,
                    message=f"Provider price updated to {req.currency} {revalidated_price}. Please confirm price change."
                )

            # Confirmed Booking
            booking = Booking(
                run_id=req.run_id,
                user_id=user_id,
                status="confirmed",
                flight_id=req.flight_id,
                hotel_id=req.hotel_id,
                quoted_price=float(req.quoted_price),
                final_price=float(revalidated_price),
                currency=req.currency,
                idempotency_key=req.idempotency_key,
            )
            session.add(booking)
            session.commit()
            session.refresh(booking)
            return self._to_response(booking, message="Trip booking confirmed successfully!")

    def list_user_bookings(self, user_id: int) -> list[BookingResponse]:
        with SessionLocal() as session:
            bookings = session.execute(
                select(Booking).where(Booking.user_id == user_id).order_by(Booking.created_at.desc())
            ).scalars().all()
            return [self._to_response(b) for b in bookings]

    def get_booking(self, booking_id: int, user_id: int) -> BookingResponse | None:
        with SessionLocal() as session:
            booking = session.execute(
                select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id)
            ).scalar_one_or_none()
            if not booking:
                return None
            return self._to_response(booking)

    def cancel_booking(self, booking_id: int, user_id: int) -> BookingResponse:
        with SessionLocal() as session:
            booking = session.execute(
                select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id)
            ).scalar_one_or_none()
            if not booking:
                raise ValueError("Booking not found or access denied")

            booking.status = "cancelled"
            session.commit()
            session.refresh(booking)
            return self._to_response(booking, message="Booking cancelled successfully")

    def _to_response(self, b: Booking, message: str | None = None) -> BookingResponse:
        return BookingResponse(
            id=b.id,
            booking_reference=b.booking_reference,
            run_id=b.run_id,
            user_id=b.user_id,
            status=b.status,
            flight_id=b.flight_id,
            hotel_id=b.hotel_id,
            quoted_price=Decimal(str(b.quoted_price)),
            final_price=Decimal(str(b.final_price)),
            currency=b.currency,
            idempotency_key=b.idempotency_key,
            created_at=b.created_at,
            message=message,
        )
