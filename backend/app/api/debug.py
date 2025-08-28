from fastapi import APIRouter, Depends
import asyncio
from app.db.bq_client import query_user, get_settings
from app.services.dependencies import get_current_user

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

@router.get("/jwt-config")
async def debug_jwt_config():
    """Endpoint de debug para verificar configuração JWT"""
    from app.config import Settings
    settings = Settings()
    return {
        "jwt_secret": settings.JWT_SECRET[:10] + "..." if settings.JWT_SECRET else "None",
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
    }

@router.post("/test-token")
async def test_token_decode(request: dict):
    """Endpoint de debug para testar decodificação de token"""
    try:
        from app.config import Settings
        import jwt
        from app.models.user import UserInDB
        
        settings = Settings()
        token = request.get("token")
        
        if not token:
            return {"error": "Token não fornecido"}
        
        # Decodificar token
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        # Tentar criar UserInDB
        user_data = {
            "id": payload.get("sub"),
            "username": "admin",
            "email": "admin@finaflow.com",
            "hashed_password": "",
            "role": payload.get("role"),
            "tenant_id": payload.get("tenant_id")
        }
        
        user = UserInDB(**user_data)
        
        return {
            "success": True,
            "payload": payload,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "tenant_id": user.tenant_id
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.get("/test-accounts")
async def test_accounts():
    """Endpoint de teste para verificar dados sem autenticação"""
    try:
        from app.db.bq_client import get_client
        client = get_client()
        
        query = """
        SELECT COUNT(*) as count
        FROM `automatizar-452311.finaflow.Accounts`
        WHERE tenant_id = 'default'
        """
        
        results = client.query(query).result()
        count = list(results)[0].count
        
        return {
            "success": True,
            "accounts_count": count,
            "message": f"Encontradas {count} contas no banco"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/temp/accounts")
async def temp_accounts():
    """Endpoint temporário para listar contas sem autenticação"""
    try:
        from app.db.bq_client import get_client
        client = get_client()
        
        query = """
        SELECT id, name, balance, created_at
        FROM `automatizar-452311.finaflow.Accounts`
        WHERE tenant_id = 'default'
        LIMIT 20
        """
        
        results = client.query(query).result()
        accounts = [dict(row) for row in results]
        
        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/temp/transactions")
async def temp_transactions():
    """Endpoint temporário para listar transações sem autenticação"""
    try:
        from app.db.bq_client import get_client
        client = get_client()
        
        query = """
        SELECT id, account_id, amount, description, created_at
        FROM `automatizar-452311.finaflow.Transactions`
        WHERE tenant_id = 'default'
        ORDER BY created_at DESC
        LIMIT 20
        """
        
        results = client.query(query).result()
        transactions = [dict(row) for row in results]
        
        return {
            "success": True,
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/temp/summary")
async def temp_summary():
    """Endpoint temporário para resumo dos dados sem autenticação"""
    try:
        from app.db.bq_client import get_client
        client = get_client()
        
        # Contar contas
        accounts_query = """
        SELECT COUNT(*) as count
        FROM `automatizar-452311.finaflow.Accounts`
        WHERE tenant_id = 'default'
        """
        accounts_result = client.query(accounts_query).result()
        accounts_count = list(accounts_result)[0].count
        
        # Contar transações
        transactions_query = """
        SELECT COUNT(*) as count
        FROM `automatizar-452311.finaflow.Transactions`
        WHERE tenant_id = 'default'
        """
        transactions_result = client.query(transactions_query).result()
        transactions_count = list(transactions_result)[0].count
        
        # Soma total das transações
        total_query = """
        SELECT SUM(CAST(amount AS FLOAT64)) as total
        FROM `automatizar-452311.finaflow.Transactions`
        WHERE tenant_id = 'default'
        """
        total_result = client.query(total_query).result()
        total_amount = list(total_result)[0].total or 0
        
        return {
            "success": True,
            "summary": {
                "accounts": accounts_count,
                "transactions": transactions_count,
                "total_amount": float(total_amount)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/routes-info")
async def routes_info():
    """Endpoint para verificar informações das rotas"""
    from fastapi import FastAPI
    from app.main import app
    
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    
    return {
        "success": True,
        "routes": routes,
        "total_routes": len(routes)
    }

@router.get("/test-auth-simple")
async def test_auth_simple(authorization: str = Header(None)):
    """Endpoint de teste simples para autenticação"""
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "No Bearer token provided"}
    
    token = authorization.replace("Bearer ", "")
    
    try:
        from app.config import Settings
        import jwt
        settings = Settings()
        
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        return {
            "success": True,
            "payload": payload,
            "message": "Token decodificado com sucesso"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
