from enum import Enum

class UserTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    BUILDING = "building"
    READY = "ready"
    DEPLOYED = "deployed"
    ERROR = "error"

class SpecFileType(str, Enum):
    DESIGN = "design"
    REQUIREMENTS = "requirements"
    TASKS = "tasks"

class AgentType(str, Enum):
    DESIGN = "design"
    BACKEND = "backend"
    TESTING = "testing"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class CodeChangeType(str, Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
