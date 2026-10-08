from decimal import Decimal
import uuid
import pytest

from app.db.models.planning_run import PlanningRun
from app.db.models.user import User
from app.db.session import SessionLocal
from app.providers.mock_booking_provider import MockBookingProvider
from app.schemas.booking import CreateBookingRequest
from app.services.booking_service import BookingService


@pytest.fixture
def test_user_and_run():
    with SessionLocal() as session:
        user = User(email=f"bkg_test_{uuid.uuid4().hex[:6]}@example.com", password_hash="pw", full_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        run = PlanningRun(
            run_id=f"run_{uuid.uuid4().hex[:6]}",
            user_id=user.id,
            status="completed",
            request_data={"destination": "Tokyo"},
            result_data={"status": "completed"},
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        yield user, run


def test_normal_booking_flow(test_user_and_run):
    user, run = test_user_and_run
    svc = BookingService(provider=MockBookingProvider())
    key = f"idem_{uuid.uuid4().hex}"

    req = CreateBookingRequest(
        run_id=run.run_id,
        flight_id="f1",
        hotel_id="h1",
        quoted_price=Decimal("150000"),
        currency="INR",
        idempotency_key=key,
    )

    res = svc.create_booking(user.id, req)
    assert res.status == "confirmed"
    assert res.quoted_price == Decimal("150000")
    assert res.booking_reference.startswith("TM-BKG-")


def test_idempotency_key_duplicate(test_user_and_run):
    user, run = test_user_and_run
    svc = BookingService(provider=MockBookingProvider())
    key = f"idem_{uuid.uuid4().hex}"

    req = CreateBookingRequest(
        run_id=run.run_id,
        quoted_price=Decimal("150000"),
        currency="INR",
        idempotency_key=key,
    )

    res1 = svc.create_booking(user.id, req)
    res2 = svc.create_booking(user.id, req)

    assert res1.id == res2.id
    assert res2.message == "Existing booking retrieved via idempotency key"


def test_price_change_requires_reconfirmation(test_user_and_run):
    user, run = test_user_and_run
    svc = BookingService(provider=MockBookingProvider(simulate_price_increase=True))
    key = f"idem_{uuid.uuid4().hex}"

    req = CreateBookingRequest(
        run_id=run.run_id,
        quoted_price=Decimal("100000"),
        currency="INR",
        idempotency_key=key,
        accept_price_change=False,
    )

    res = svc.create_booking(user.id, req)
    assert res.status == "price_changed"
    assert res.final_price > res.quoted_price


def test_cancel_booking(test_user_and_run):
    user, run = test_user_and_run
    svc = BookingService(provider=MockBookingProvider())
    key = f"idem_{uuid.uuid4().hex}"

    req = CreateBookingRequest(
        run_id=run.run_id,
        quoted_price=Decimal("100000"),
        currency="INR",
        idempotency_key=key,
    )

    res = svc.create_booking(user.id, req)
    cancelled = svc.cancel_booking(res.id, user.id)
    assert cancelled.status == "cancelled"
