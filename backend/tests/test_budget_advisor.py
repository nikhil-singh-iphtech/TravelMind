from datetime import date
from decimal import Decimal
import pytest

from app.core.budget_advisor import BudgetAdvisor
from app.schemas import Activity, Flight, Hotel, BudgetResult, ConstraintResult
from app.schemas.state import TravelRequest, TravelState


def test_budget_advisor_within_budget():
    req = TravelRequest(
        origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
        travellers=2, duration_days=7, budget=Decimal("300000"), currency="INR"
    )
    state = TravelState(request=req)
    state.flights = [Flight(id="f1", airline="IndiGo", price=Decimal("60000"), currency="INR")]
    state.hotels = [Hotel(id="h1", name="Hotel A", city="Tokyo", price_per_night=Decimal("8000"), nights=7, currency="INR")]
    state.selected_flight = state.flights[0]
    state.selected_hotel = state.hotels[0]
    state.budget_result = BudgetResult(total=Decimal("150000"), budget=Decimal("300000"), passed=True)

    advice = BudgetAdvisor().analyze(req, state)
    assert advice.status == "within_budget"
    assert advice.gap == Decimal("150000")


def test_budget_advisor_reducible_suggestions():
    req = TravelRequest(
        origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
        travellers=2, duration_days=7, budget=Decimal("150000"), currency="INR"
    )
    state = TravelState(request=req)
    state.flights = [
        Flight(id="f1", airline="Expensive Air", price=Decimal("100000"), currency="INR"),
        Flight(id="f2", airline="Budget Air", price=Decimal("50000"), currency="INR"),
    ]
    state.hotels = [
        Hotel(id="h1", name="Luxury Hotel", city="Tokyo", price_per_night=Decimal("15000"), nights=7, currency="INR"),
        Hotel(id="h2", name="Hostel B", city="Tokyo", price_per_night=Decimal("4000"), nights=7, currency="INR"),
    ]
    state.activities = [Activity(id="a1", name="Fancy Tour", price=Decimal("20000"), currency="INR")]

    # Currently chosen expensive option: total = 100000 + (15000*7=105000) + 20000 + transport + food > 200000
    state.selected_flight = state.flights[0]
    state.selected_hotel = state.hotels[0]
    state.budget_result = BudgetResult(total=Decimal("240000"), budget=Decimal("150000"), passed=False)

    advice = BudgetAdvisor().analyze(req, state)
    assert advice.status == "reducible"
    assert len(advice.suggestions) > 0
    components = [s.component for s in advice.suggestions]
    assert "flight" in components or "hotel" in components or "activities" in components


def test_budget_advisor_increase_needed():
    req = TravelRequest(
        origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
        travellers=2, duration_days=7, budget=Decimal("20000"), currency="INR" # impossibly low budget
    )
    state = TravelState(request=req)
    state.flights = [Flight(id="f1", airline="Air A", price=Decimal("80000"), currency="INR")]
    state.hotels = [Hotel(id="h1", name="Hotel A", city="Tokyo", price_per_night=Decimal("10000"), nights=7, currency="INR")]
    state.selected_flight = state.flights[0]
    state.selected_hotel = state.hotels[0]
    state.budget_result = BudgetResult(total=Decimal("170000"), budget=Decimal("20000"), passed=False)

    advice = BudgetAdvisor().analyze(req, state)
    assert advice.status == "increase_needed"
    assert advice.recommended_budget > Decimal("20000")
