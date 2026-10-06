from decimal import Decimal

from pydantic import BaseModel


class Flight(BaseModel):
    id: str
    airline: str
    price: Decimal
    currency: str = "INR"


class Hotel(BaseModel):
    id: str
    name: str
    city: str
    price_per_night: Decimal
    nights: int
    currency: str = "INR"

    @property
    def total_price(self) -> Decimal:
        return self.price_per_night * self.nights


class Activity(BaseModel):
    id: str
    name: str
    price: Decimal
    currency: str = "INR"