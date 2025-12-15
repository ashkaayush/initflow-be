from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models.marketplace import MarketplaceComponent, ComponentIntegration
from app.models import User
from app.auth import get_current_user

router = APIRouter()

# Mock component data
MOCK_COMPONENTS = [
    {
        "id": "auth-template",
        "name": "Authentication Template",
        "description": "Complete authentication system with login, signup, and password reset",
        "category": "Authentication",
        "tags": ["auth", "login", "security"],
        "preview_url": "https://example.com/preview/auth",
        "spec_template": {"requirements": "User auth with email/password"},
        "code_template": {"screens/LoginScreen.js": "// Login screen"},
        "dependencies": ["@react-native-async-storage/async-storage"],
        "downloads": 1250,
        "rating": 4.8,
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "payment-module",
        "name": "Payment Integration",
        "description": "Stripe payment integration with card processing",
        "category": "Payments",
        "tags": ["stripe", "payments", "checkout"],
        "preview_url": "https://example.com/preview/payments",
        "spec_template": {"requirements": "Stripe integration"},
        "code_template": {"services/stripe.js": "// Stripe code"},
        "dependencies": ["@stripe/stripe-react-native"],
        "downloads": 890,
        "rating": 4.6,
        "created_at": "2024-01-15T00:00:00Z"
    }
]

# --- Search marketplace ---
@router.get("/search", response_model=List[MarketplaceComponent])
async def search_marketplace(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None)
):
    results = MOCK_COMPONENTS
    
    if query:
        q = query.lower()
        results = [c for c in results if q in c["name"].lower() or q in c["description"].lower()]
    
    if category:
        results = [c for c in results if c["category"].lower() == category.lower()]
    
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",")]
        results = [c for c in results if any(tag in [t.lower() for t in c["tags"]] for tag in tag_list)]
    
    return [MarketplaceComponent(**c) for c in results]

# --- Get component details ---
@router.get("/components/{component_id}", response_model=MarketplaceComponent)
async def get_component(component_id: str):
    component = next((c for c in MOCK_COMPONENTS if c["id"] == component_id), None)
    if not component:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
    return MarketplaceComponent(**component)

# --- Integrate component into a project ---
@router.post("/projects/{project_id}/integrate")
async def integrate_component(
    project_id: str,
    integration: ComponentIntegration,
    current_user: User = Depends(get_current_user)
):
    # In production, this would update spec files and generate code in E2B sandbox
    return {
        "message": f"Component '{integration.component_id}' integrated successfully into project '{project_id}'",
        "project_id": project_id
    }
