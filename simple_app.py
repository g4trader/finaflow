from fastapi import FastAPI
import uvicorn

app = FastAPI(title="FinaFlow Backend", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Starting FinaFlow Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8080)