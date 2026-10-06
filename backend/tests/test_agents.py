from decimal import Decimal

import pytest

from app.agents import (
    ActivityAgent, ActivityAgentInput,
    BudgetAgent, BudgetAgentInput,
    ConstraintAgent, ConstraintAgentInput,
    FlightAgent, FlightAgentInput,
    WeatherAgent, WeatherAgentInput,
)
from app.schemas import Activity, Flight, Hotel
from tests.fakes import FakeToolProvider


async def test_flight_agent_returns_flights():
    llm = FakeToolProvider(
        tool_name="search_flights",
        arguments={"origin": "Delhi", "destination": "Tokyo", "departure_date": "2026-11-01", "travellers": 2},
        final_text="IndiGo is cheapest.",
    )
    result = await FlightAgent(llm).run(
        FlightAgentInput(origin="Delhi", destination="Tokyo", departure_date="2026-11-01", travellers=2)
    )

    assert result.success is True
    assert len(result.data.flights) == 2
    assert result.data.reasoning == "IndiGo is cheapest."


async def test_activity_agent_returns_activities():
    llm = FakeToolProvider(tool_name="search_activities", arguments={"city": "Tokyo"})
    result = await ActivityAgent(llm).run(ActivityAgentInput(city="Tokyo"))

    assert result.success is True
    assert len(result.data.activities) == 3


async def test_weather_agent_returns_weather_from_tool():
    llm = FakeToolProvider(
        tool_name="get_weather",
        arguments={"city": "Tokyo", "target_date": "2026-11-01"},
        final_text="Clear and mild.",
    )
    result = await WeatherAgent(llm).run(WeatherAgentInput(city="Tokyo", target_date="2026-11-01"))

    assert result.success is True
    assert result.data.weather.city == "Tokyo"
    assert result.data.summary == "Clear and mild."


async def test_agent_fails_safely_when_model_skips_the_tool():
    llm = FakeToolProvider()  # never calls the tool
    result = await FlightAgent(llm).run(
        FlightAgentInput(origin="Delhi", destination="Tokyo", departure_date="2026-11-01", travellers=2)
    )

    assert result.success is False
    assert "without calling search_flights" in result.error


async def test_agent_fails_safely_on_invalid_tool_arguments():
    llm = FakeToolProvider(tool_name="search_flights", arguments={"origin": "Delhi"})  # missing fields
    result = await FlightAgent(llm).run(
        FlightAgentInput(origin="Delhi", destination="Tokyo", departure_date="2026-11-01", travellers=2)
    )

    assert result.success is False


def _sample_plan():
    flights = [Flight(id="f1", airline="IndiGo", price=Decimal("80000"))]
    hotels = [Hotel(id="h1", name="Hotel A", city="Tokyo", price_per_night=Decimal("15000"), nights=10)]
    activities = [Activity(id="a1", name="Tour", price=Decimal("5000"))]
    return flights, hotels, activities


async def test_budget_agent_verdict_comes_from_python_not_the_llm():
    flights, hotels, activities = _sample_plan()
    agent = BudgetAgent(llm=FakeToolProvider())  # fake LLM says "Fake explanation."

    result = await agent.run(
        BudgetAgentInput(budget=Decimal("200000"), flights=flights, hotels=hotels, activities=activities)
    )

    assert result.data.result.total == Decimal("235000")
    assert result.data.result.passed is False
    assert result.data.explanation == "Fake explanation."


async def test_budget_agent_works_without_an_llm():
    flights, hotels, activities = _sample_plan()

    result = await BudgetAgent(llm=None).run(
        BudgetAgentInput(budget=Decimal("300000"), flights=flights, hotels=hotels, activities=activities)
    )

    assert result.data.result.passed is True


async def test_constraint_agent_reports_violations():
    _, hotels, _ = _sample_plan()

    result = await ConstraintAgent(llm=None).run(
        ConstraintAgentInput(
            total_cost=Decimal("235000"),
            budget=Decimal("200000"),
            hotels=hotels,
            max_hotel_price_per_night=Decimal("10000"),
            travellers=2,
            expected_travellers=2,
            duration_days=7,
            expected_duration_days=7,
        )
    )

    assert result.data.result.passed is False
    names = {v.constraint for v in result.data.result.violations}
    assert "budget" in names
    assert "hotel_price:h1" in names