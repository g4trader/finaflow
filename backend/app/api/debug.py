from fastapi import APIRouter
import asyncio
from app.db.bq_client import query_user, get_settings

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/user/{username}")
async def debug_user(username: str):
    """Endpoint de debug para verificar usuário no banco"""
    try:
        results = await asyncio.to_thread(query_user, username)
        return {
            "username": username,
            "found": len(results) > 0,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "username": username,
            "error": str(e),
            "found": False
        }

@router.get("/config")
async def debug_config():
    """Endpoint de debug para verificar configurações do banco"""
    try:
        settings = get_settings()
        return {
            "project_id": settings.PROJECT_ID,
            "dataset": settings.DATASET,
            "table": "Users",
            "full_table": f"{settings.PROJECT_ID}.{settings.DATASET}.Users"
        }
    except Exception as e:
        return {
            "error": str(e)
        }

@router.get("/auth-test")
async def debug_auth_test(current=Depends(get_current_user)):
    """Endpoint de debug para testar autenticação"""
    return {
        "authenticated": True,
        "user_id": current.id,
        "username": current.username,
        "role": current.role,
        "tenant_id": current.tenant_id
    }
