from datetime import date
from decimal import Decimal

from pydantic import BaseModel, model_validator


class HotelSearchInput(BaseModel):
    city: str
    check_in: date
    check_out: date
    guests: int
    max_price_per_night: Decimal
    currency: str = "INR"

    @model_validator(mode="after")
    def check_dates(self) -> "HotelSearchInput":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self


class FlightSearchInput(BaseModel):
    origin: str
    destination: str
    departure_date: date
    travellers: int
    currency: str = "INR"


class ActivitySearchInput(BaseModel):
    city: str
    interests: list[str] = []
    max_price: Decimal | None = None


class WeatherInput(BaseModel):
    city: str
    target_date: date