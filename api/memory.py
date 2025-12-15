from typing import List
from app.models.memory import MemoryItem
from app.database import get_supabase
import uuid
from datetime import datetime

class MemoryService:
    """Project memory management for AI context"""

    def __init__(self):
        self.supabase = get_supabase()

    async def store_conversation(self, project_id: str, role: str, content: str) -> MemoryItem:
        """Store a memory item"""
        memory_id = str(uuid.uuid4())
        item = {
            "id": memory_id,
            "project_id": project_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow()
        }
        self.supabase.table("project_memory").insert(item).execute()
        return MemoryItem(**item)

    async def get_project_memory(self, project_id: str, limit: int = 50) -> List[MemoryItem]:
        """Retrieve recent memory items for a project"""
        response = self.supabase.table("project_memory")\
            .select("*")\
            .eq("project_id", project_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return [MemoryItem(**item) for item in reversed(response.data)] if response.data else []

    async def clear_project_memory(self, project_id: str):
        """Clear all memory for a project"""
        self.supabase.table("project_memory").delete().eq("project_id", project_id).execute()
        return {"message": f"Memory cleared for project {project_id}"}


# Singleton instance
memory_service = MemoryService()
