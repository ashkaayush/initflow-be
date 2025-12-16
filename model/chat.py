from pydantic import BaseModel
from typing import Optional, List

class ChatMessage(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    id: str
    project_id: str
    role: str
    content: str
    attachments: Optional[List[str]] = None

class MemoryItem(BaseModel):
    role: str
    content: str
