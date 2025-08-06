from fastapi import FastAPI

app = FastAPI(title="FinaFlow Backend")

@app.get("/healthz", tags=["health"])
async def health_check():
    return {"status": "ok"}
