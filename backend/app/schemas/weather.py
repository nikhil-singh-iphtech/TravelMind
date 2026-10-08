from datetime import date

from pydantic import BaseModel


class WeatherInfo(BaseModel):
    city: str
    target_date: date
    temperature_celsius: float | None = None
    condition: str