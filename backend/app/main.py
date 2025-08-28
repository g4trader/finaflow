from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.api import auth, include_routers, debug, debug_auth
from app.db.bq_client import get_client

app = FastAPI(title="FinaFlow Backend")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://finaflow.vercel.app",  # Frontend em produção
        "https://finaflow-qu0b1xjlo-south-medias-projects.vercel.app",  # URL alternativa do Vercel
        "http://localhost:3000",  # Frontend local
        "http://localhost:3001",  # Frontend local alternativo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(debug.router)
app.include_router(debug_auth.router)
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
