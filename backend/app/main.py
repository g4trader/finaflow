from fastapi import FastAPI
from app.api.auth import router as auth_router

app = FastAPI(title="FinaFlow Backend")

app.include_router(auth_router)

@app.get("/healthz", tags=["health"])
async def health_check():
    return {"status": "ok"}
