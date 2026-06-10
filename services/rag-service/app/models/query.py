from typing import List, Optional

from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=3, ge=1, le=10)


class RetrievedSource(BaseModel):
    document_id: str
    chunk_id: str
    score: float
    text: str


class RagQueryResponse(BaseModel):
    answer: str
    query: str
    top_k: int
    sources: List[RetrievedSource]
    cached: bool = False


class RetrieveResponse(BaseModel):
    query: str
    top_k: int
    sources: List[RetrievedSource]