from decimal import Decimal

from app.schemas.state import TravelRequest

# Deterministic business rules. Never decided by the LLM, per project rules.
HOTEL_BUDGET_SHARE = Decimal("0.4")
FOOD_PER_PERSON_PER_DAY = Decimal("2000")
TRANSPORT_PER_PERSON_PER_DAY = Decimal("500")


def hotel_cap(request: TravelRequest) -> Decimal:
    """Max hotel price per night: the user's cap, or a share of the budget."""
    if request.max_hotel_price_per_night is not None:
        return request.max_hotel_price_per_night
    return (request.budget * HOTEL_BUDGET_SHARE / request.duration_days).quantize(Decimal("1"))