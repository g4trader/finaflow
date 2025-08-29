from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

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
    return {"message": "FinaFlow Backend API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "finaflow-backend"}

@app.get("/api/v1/test")
async def test():
    return {"message": "API funcionando!"}

@app.post("/auth/login")
async def login():
    return {
        "access_token": "test-token",
        "refresh_token": "test-refresh",
        "token_type": "bearer",
        "expires_in": 1800
    }

@app.get("/api/v1/transactions")
async def get_transactions():
    return {
        "transactions": [
            {"id": 1, "description": "Vendas Cursos", "amount": 1000.00, "type": "credit"},
            {"id": 2, "description": "Salário", "amount": 5000.00, "type": "debit"}
        ]
    }

@app.get("/api/v1/reports/cash-flow")
async def get_cash_flow():
    return {
        "cash_flow": [
            {"month": "Jan", "income": 50000, "expense": 30000, "balance": 20000},
            {"month": "Fev", "income": 60000, "expense": 35000, "balance": 25000}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
