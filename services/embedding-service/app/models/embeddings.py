from typing import List, Union

from pydantic import BaseModel, ConfigDict, Field


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]] = Field(...)
    normalize: bool | None = None


class EmbeddingData(BaseModel):
    index: int
    embedding: List[float]


class EmbeddingUsage(BaseModel):
    input_count: int
    embedding_dimensions: int


class EmbeddingResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    data: List[EmbeddingData]
    usage: EmbeddingUsage