from fastapi import FastAPI, HTTPException
from datetime import datetime
from app.api import auth, include_routers
from app.db.bq_client import get_client

app = FastAPI(title="FinaFlow Backend")

app.include_router(auth.router)
include_routers(app)

@app.get("/healthz", tags=["health"])
async def health_check():
    try:
        # Verificar conexão com BigQuery
        client = get_client()
        if hasattr(client, 'project'):
            project_id = client.project
        return {
            "status": "healthy",
            "database": "connected" if hasattr(client, 'project') else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unhealthy")
