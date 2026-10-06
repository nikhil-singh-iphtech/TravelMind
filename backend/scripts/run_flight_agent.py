import asyncio
import json

from app.agents import FlightAgent, FlightAgentInput
from app.llm.groq_provider import GroqProvider


async def main():
    agent = FlightAgent(llm=GroqProvider())
    result = await agent.run(
        FlightAgentInput(
            origin="Delhi",
            destination="Tokyo",
            departure_date="2026-11-01",
            travellers=2,
        )
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())