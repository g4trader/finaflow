from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import os
from contextlib import asynccontextmanager

from app.database import create_tables
from app.api import auth, financial, test_auth, import_api
from app.routes import permissions
from app.models.auth import Base
from app.models.financial import Base as FinancialBase

# Configurações de segurança
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,finaflow.vercel.app").split(",")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://finaflow.vercel.app,http://localhost:3000").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle da aplicação."""
    # Startup
    print("🚀 Iniciando FinaFlow Backend...")
    create_tables()
    print("✅ Tabelas criadas com sucesso")
    
    yield
    
    # Shutdown
    print("🛑 Encerrando FinaFlow Backend...")

# Criar aplicação FastAPI
app = FastAPI(
    title="FinaFlow API",
    description="API de gestão financeira empresarial SaaS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware de segurança
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware de logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para log de requests."""
    start_time = time.time()
    
    # Processar request
    response = await call_next(request)
    
    # Calcular tempo de resposta
    process_time = time.time() - start_time
    
    # Log da requisição
    print(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# Middleware de tratamento de erros
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    print(f"❌ Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )

# Health check
@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {
        "status": "healthy",
        "service": "finaflow-backend",
        "version": "1.0.0"
    }

# Incluir routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(financial.router, prefix="/api/v1")
app.include_router(test_auth.router, prefix="/api/v1")
app.include_router(import_api.router, prefix="/api/v1")
app.include_router(permissions.router)

# Rota raiz
@app.get("/")
async def root():
    """Rota raiz da API."""
    return {
        "message": "FinaFlow API - Sistema de Gestão Financeira",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
