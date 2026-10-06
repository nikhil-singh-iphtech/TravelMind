import asyncio
from typing import Sequence

from sqlalchemy import select

from app.db.models.document_chunk import DocumentChunk
from app.db.session import SessionLocal
from app.embeddings.base import EmbeddingProvider
from app.schemas.rag import GuideChunk, RetrievedChunk


class RetrieverService:
    """
    Stores and searches small text chunks using pgvector similarity
    search. DB calls are sync (Phase 2's SessionLocal), so they're
    wrapped in asyncio.to_thread to avoid blocking the event loop
    every other agent and tool in this system relies on.
    """

    def __init__(self, embedding_provider: EmbeddingProvider):
        self.embeddings = embedding_provider

    async def ingest(self, chunks: Sequence[GuideChunk]) -> int:
        vectors = self.embeddings.embed([c.content for c in chunks])
        return await asyncio.to_thread(self._ingest_sync, chunks, vectors)

    def _ingest_sync(self, chunks: Sequence[GuideChunk], vectors: list[list[float]]) -> int:
        with SessionLocal() as session:
            for chunk, vector in zip(chunks, vectors):
                session.add(DocumentChunk(
                    source=chunk.source, city=chunk.city, content=chunk.content, embedding=vector,
                ))
            session.commit()
        return len(chunks)

    async def retrieve(self, query: str, city: str | None = None, top_k: int = 3) -> list[RetrievedChunk]:
        [query_vector] = self.embeddings.embed([query])
        return await asyncio.to_thread(self._retrieve_sync, query_vector, city, top_k)

    def _retrieve_sync(self, query_vector: list[float], city: str | None, top_k: int) -> list[RetrievedChunk]:
        with SessionLocal() as session:
            distance = DocumentChunk.embedding.cosine_distance(query_vector)
            stmt = select(DocumentChunk, distance.label("distance"))
            if city:
                stmt = stmt.where(DocumentChunk.city == city)
            stmt = stmt.order_by("distance").limit(top_k)

            rows = session.execute(stmt).all()
            return [
                RetrievedChunk(content=row.DocumentChunk.content, source=row.DocumentChunk.source, score=row.distance)
                for row in rows
            ]