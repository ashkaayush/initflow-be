from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from app.models.chat import ChatMessage, ChatMessageResponse
from app.auth import get_current_user
from app.models import User
from app.database import get_supabase
from app.services.memory_service import memory_service
from app.services.ai_service import ai_service

router = APIRouter()

# Helper to get project context
async def get_project_context(project_id: str):
    supabase = get_supabase()
    
    # Project info
    project = supabase.table("projects").select("name, description").eq("id", project_id).execute()
    project_info = project.data[0] if project.data else {}

    # Recent memory
    recent_memory = await memory_service.get_project_memory(project_id)

    # Specs
    specs_resp = supabase.table("spec_files").select("file_type, content").eq("project_id", project_id).execute()
    spec_context = {spec["file_type"]: spec["content"][:500]+"..." for spec in specs_resp.data} if specs_resp.data else {}

    return project_info, recent_memory, spec_context


@router.post("", response_model=ChatMessageResponse)
async def send_message(project_id: str, message: ChatMessage, current_user: User = Depends(get_current_user)):
    supabase = get_supabase()

    # Verify project access
    project_resp = supabase.table("projects").select("user_id").eq("id", project_id).execute()
    if not project_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project_resp.data[0]["user_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Store user message
    user_message_id = str(uuid.uuid4())
    user_data = {
        "id": user_message_id,
        "project_id": project_id,
        "role": "user",
        "content": message.message
    }
    supabase.table("chat_messages").insert(user_data).execute()
    await memory_service.store_conversation(project_id, "user", message.message)

    # Get context and AI response
    project_info, recent_memory, spec_context = await get_project_context(project_id)
    context = {"project_info": project_info, "recent_memory": recent_memory[:5], "spec_context": spec_context}

    ai_response_text = await ai_service.generate_response(current_user, message.message, context, "System: AI assistant for mobile apps", project_id)

    # Store AI response
    ai_message_id = str(uuid.uuid4())
    ai_data = {
        "id": ai_message_id,
        "project_id": project_id,
        "role": "assistant",
        "content": ai_response_text
    }
    resp = supabase.table("chat_messages").insert(ai_data).execute()
    await memory_service.store_conversation(project_id, "assistant", ai_response_text)

    return ChatMessageResponse(**resp.data[0])


@router.get("/history", response_model=List[ChatMessageResponse])
async def get_chat_history(project_id: str, current_user: User = Depends(get_current_user)):
    supabase = get_supabase()
    project_resp = supabase.table("projects").select("user_id").eq("id", project_id).execute()
    if not project_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project_resp.data[0]["user_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    messages_resp = supabase.table("chat_messages").select("*").eq("project_id", project_id).order("created_at", desc=False).execute()
    return [ChatMessageResponse(**msg) for msg in messages_resp.data]
