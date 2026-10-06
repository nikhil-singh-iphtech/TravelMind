from pydantic import BaseModel


class GuideChunk(BaseModel):
    """One piece of source text, ready to be embedded and stored."""
    source: str
    city: str | None = None
    content: str


class RetrievedChunk(BaseModel):
    """One piece of retrieved context, with its similarity score."""
    content: str
    source: str
    score: float  # cosine distance — lower means more similar