from typing import Optional
from pydantic import BaseModel

class RagQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4