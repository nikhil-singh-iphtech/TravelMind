import operator
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.results import BudgetResult, ConstraintResult, Itinerary
from app.schemas.state import TravelRequest, WorkflowEvent
from app.schemas.travel import Activity, Flight, Hotel
from app.schemas.weather import WeatherInfo


class GraphState(BaseModel):
    """
    Same shape as TravelState, with one real difference: errors and
    events are Annotated with operator.add, so when several parallel
    nodes each return their own list, LangGraph CONCATENATES them
    instead of letting the last one silently overwrite the rest.

    Every other field is written by exactly one node at a time, so
    the default reducer (overwrite) is correct for them.
    """

    run_id: str = ""
    request: TravelRequest

    strategy: str = "comfort"
    status: str = "running"
    preferences: str | None = None

    flights: list[Flight] = []
    hotels: list[Hotel] = []
    activities: list[Activity] = []
    weather: WeatherInfo | None = None

    selected_flight: Flight | None = None
    selected_hotel: Hotel | None = None

    budget_result: BudgetResult | None = None
    constraint_result: ConstraintResult | None = None
    itinerary: Itinerary | None = None

    iteration: int = 0
    errors: Annotated[list[str], operator.add] = Field(default_factory=list)
    events: Annotated[list[WorkflowEvent], operator.add] = Field(default_factory=list)