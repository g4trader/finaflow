"""Debug endpoints for authentication testing."""

from fastapi import APIRouter, Depends, Header
from app.services.dependencies import get_current_user, tenant

router = APIRouter(prefix="/debug-auth", tags=["debug-auth"])

@router.get("/test-get-current-user")
async def test_get_current_user(current=Depends(get_current_user)):
    """Endpoint de teste para get_current_user"""
    return {
        "success": True,
        "user": {
            "id": current.id,
            "username": current.username,
            "role": current.role,
            "tenant_id": current.tenant_id
        }
    }

@router.get("/test-tenant")
async def test_tenant(tenant_id: str = Depends(tenant)):
    """Endpoint de teste para função tenant"""
    return {
        "success": True,
        "tenant_id": tenant_id
    }

@router.get("/test-both")
async def test_both(current=Depends(get_current_user), tenant_id: str = Depends(tenant)):
    """Endpoint de teste para ambas as funções"""
    return {
        "success": True,
        "user": {
            "id": current.id,
            "username": current.username,
            "role": current.role,
            "tenant_id": current.tenant_id
        },
        "tenant_id": tenant_id
    }
