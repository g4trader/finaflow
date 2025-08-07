from fastapi import FastAPI
from app.api import auth, include_routers

app = FastAPI(title="FinaFlow Backend")

app.include_router(auth.router)
include_routers(app)

@app.get("/healthz", tags=["health"])
async def health_check():
    return {"status": "ok"}
