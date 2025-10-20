from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://finaflow.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "FinaFlow Backend API"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "finaflow-backend"}

@app.get("/api/v1/test")
async def test():
    return {"message": "API funcionando!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
