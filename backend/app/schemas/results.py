from decimal import Decimal

from pydantic import BaseModel


class BudgetResult(BaseModel):
    total: Decimal
    budget: Decimal
    passed: bool


class ConstraintViolation(BaseModel):
    constraint: str
    expected: str
    actual: str


class ConstraintResult(BaseModel):
    passed: bool
    violations: list[ConstraintViolation] = []


class Itinerary(BaseModel):
    destination: str
    duration_days: int
    total_cost: Decimal
    currency: str = "INR"
    summary: str