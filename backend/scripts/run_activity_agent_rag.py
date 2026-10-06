import asyncio
import json

from app.agents.activity import ActivityAgent, ActivityAgentInput
from app.embeddings.local_provider import SentenceTransformerProvider
from app.llm.groq_provider import GroqProvider
from app.services.retriever_service import RetrieverService


async def main():
    retriever = RetrieverService(SentenceTransformerProvider())
    agent = ActivityAgent(llm=GroqProvider(), retriever=retriever)

    result = await agent.run(ActivityAgentInput(city="Tokyo", interests=["culture", "outdoor"]))
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())