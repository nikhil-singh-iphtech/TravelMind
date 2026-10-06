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