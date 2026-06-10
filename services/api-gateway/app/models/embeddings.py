from typing import List, Union
from pydantic import BaseModel

class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str