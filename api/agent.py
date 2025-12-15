from fastapi import APIRouter, Depends
from app.models import TaskCreate, User
from app.auth import get_current_user
from app.services.agno_agent import AgnoAgent

router = APIRouter()

@router.post("/tasks/run")
async def run_ai_task(project_id: str, task_data: TaskCreate, current_user: User = Depends(get_current_user)):
    """
    Submit a task to the AI agent (Agno framework)
    """
    agent = AgnoAgent(current_user)

    # Optional: Get project context (spec files, recent memory)
    context = {}  # Could fetch from memory_service / spec files

    result = await agent.generate_code(project_id, task_data.description, task_data.agent_type, context)

    # Apply generated files to sandbox
    for path, content in result["files"].items():
        await agent.apply_change_to_sandbox(project_id, path, content)

    return {
        "message": "AI task completed",
        "files_generated": list(result["files"].keys()),
        "reasoning": result["reasoning"]
    }
