import asyncio
from pathlib import Path

from app.core.chunking import chunk_text
from app.embeddings.local_provider import SentenceTransformerProvider
from app.schemas.rag import GuideChunk
from app.services.retriever_service import RetrieverService

GUIDES_DIR = Path(__file__).resolve().parent.parent / "data" / "guides"


async def main():
    retriever = RetrieverService(SentenceTransformerProvider())

    all_chunks: list[GuideChunk] = []
    for path in sorted(GUIDES_DIR.glob("*.md")):
        city = path.stem.capitalize()
        text = path.read_text()
        for piece in chunk_text(text):
            all_chunks.append(GuideChunk(source=path.name, city=city, content=piece))

    count = await retriever.ingest(all_chunks)
    print(f"Ingested {count} chunks from {GUIDES_DIR}")


if __name__ == "__main__":
    asyncio.run(main())