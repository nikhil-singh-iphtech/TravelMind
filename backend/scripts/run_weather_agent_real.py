# scripts/run_weather_agent_real.py
import asyncio
import json
from datetime import date, timedelta

from app.agents import WeatherAgent, WeatherAgentInput
from app.llm.groq_provider import GroqProvider


async def main():
    agent = WeatherAgent(llm=GroqProvider())
    target = (date.today() + timedelta(days=3)).isoformat()

    result = await agent.run(WeatherAgentInput(city="Tokyo", target_date=target))
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())