from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class Preference(BaseModel):
    key: str
    value: str


class TripRecord(BaseModel):
    destination: str
    start_date: date
    duration_days: int
    travellers: int
    total_cost: Decimal
    currency: str
    summary: str
    created_at: datetime