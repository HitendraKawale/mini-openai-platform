from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class Messagge(BaseModel):
    role: Literal['system', 'user', 'assistant']
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "auto"
    messages: List[Messagge]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 256
    stream: Optional[bool] = False