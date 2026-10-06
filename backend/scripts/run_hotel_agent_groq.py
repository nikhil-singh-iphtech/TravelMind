import asyncio
import json

from app.agents.hotel import HotelAgent, HotelAgentInput
from app.llm.groq_provider import GroqProvider


async def main():
    agent = HotelAgent(llm=GroqProvider())  # only this line differs from the Gemini script

    result = await agent.run(
        HotelAgentInput(
            city="Tokyo",
            check_in="2026-11-01",
            check_out="2026-11-08",
            guests=2,
            max_price_per_night=12000.0,
        )
    )

    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())