from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MemoryItem(BaseModel):
    id: str
    project_id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: Optional[datetime] = None

class MemoryStore(BaseModel):
    project_id: str
    role: str
    content: str

class MemoryResponse(BaseModel):
    memory: List[MemoryItem]
