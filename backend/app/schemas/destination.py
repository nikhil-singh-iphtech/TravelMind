from pydantic import BaseModel, HttpUrl


class DestinationResource(BaseModel):
    title: str
    url: str
    source_site: str
    snippet: str
