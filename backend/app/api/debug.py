from fastapi import APIRouter
import asyncio
from app.db.bq_client import query_user

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
