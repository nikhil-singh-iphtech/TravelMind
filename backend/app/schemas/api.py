from typing import Literal

from pydantic import BaseModel

from app.schemas.state import TravelRequest


class PlanRequest(BaseModel):
    """
    API-only envelope around a TravelRequest. user_id and engine are
    transport/API concerns, not facts about the trip itself, so they
    stay out of TravelRequest — same boundary discipline as every
    other schema split in this project.
    """
    trip: TravelRequest
    user_id: int | None = None
    engine: Literal["custom", "langgraph"] = "custom"


class RefineRequest(BaseModel):
    """
    Interactive plan refinement parameters allowing users to swap selected flights,
    hotels, toggle activities, or update budget targets.
    """
    flight_id: str | None = None
    hotel_id: str | None = None
    excluded_activity_ids: list[str] = []
    custom_budget: float | None = None