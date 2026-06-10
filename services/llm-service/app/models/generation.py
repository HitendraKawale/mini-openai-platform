from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GenerationRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    prompt: str = Field(..., min_length=1)
    max_new_tokens: Optional[int] = Field(default=128, ge=1, le=512)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    do_sample: Optional[bool] = True
    model: Optional[str] = Field(
        default=None,
        description="Explicit model name, or 'auto'/None to let the router decide",
    )


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class RoutingInfo(BaseModel):
    decision: str
    difficulty: Optional[float] = None
    fallback_used: bool = False


class GenerationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    generated_text: str
    model_name: str
    usage: TokenUsage
    routing: Optional[RoutingInfo] = None