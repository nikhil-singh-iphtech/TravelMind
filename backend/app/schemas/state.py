from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.schemas.budget_advice import BudgetAdvice
from app.schemas.destination import DestinationResource
from app.schemas.results import BudgetResult, ConstraintResult, Itinerary
from app.schemas.travel import Activity, Flight, Hotel
from app.schemas.weather import WeatherInfo


class TravelRequest(BaseModel):
    """The structured trip request. (Request Agent will produce this later.)"""

    origin: str
    destination: str
    start_date: date
    travellers: int = Field(gt=0)
    duration_days: int = Field(gt=0)
    budget: Decimal = Field(gt=0)
    currency: str = "INR"
    interests: list[str] = []
    max_hotel_price_per_night: Decimal | None = None


class WorkflowEvent(BaseModel):
    """One thing that happened during a run. The UI will stream these later."""

    run_id: str
    event_type: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TravelState(BaseModel):
    """
    Everything the workflow knows about one planning run.

    Pydantic copies mutable defaults (the [] below) for every new
    instance, so two states never share the same list.
    """

    run_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    request: TravelRequest

    strategy: str = "comfort"  # "comfort" = priciest options, "budget" = cheapest
    status: str = "running"  # running | completed | failed

    # Research results (candidates)
    flights: list[Flight] = []
    hotels: list[Hotel] = []
    activities: list[Activity] = []
    weather: WeatherInfo | None = None

    # Python's choices from the candidates
    selected_flight: Flight | None = None
    selected_hotel: Hotel | None = None

    # Deterministic verdicts
    budget_result: BudgetResult | None = None
    constraint_result: ConstraintResult | None = None
    itinerary: Itinerary | None = None
    budget_advice: BudgetAdvice | None = None
    destination_resources: list[DestinationResource] = []

    iteration: int = 0  # number of replans (used from Phase 9)
    errors: list[str] = []
    events: list[WorkflowEvent] = []