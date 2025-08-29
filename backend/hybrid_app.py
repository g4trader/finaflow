from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import jwt
import datetime

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

@app.post("/api/v1/auth/login")
async def login():
    # Criar um JWT simples para teste
    payload = {
        "sub": "1",
        "username": "admin",
        "email": "admin@finaflow.com",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
        "tenant_id": "1",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    # Usar uma chave secreta simples para teste
    secret_key = "finaflow-secret-key-2024"
    
    access_token = jwt.encode(payload, secret_key, algorithm="HS256")
    
    return {
        "access_token": access_token,
        "refresh_token": "test-refresh-token",
        "token_type": "bearer",
        "expires_in": 1800
    }

@app.get("/api/v1/financial/transactions")
async def get_transactions():
    return [
        {"id": 1, "description": "Vendas Cursos", "amount": 1000.00, "type": "credit"},
        {"id": 2, "description": "Salário", "amount": 5000.00, "type": "debit"}
    ]

@app.get("/api/v1/financial/accounts")
async def get_accounts():
    return [
        {"id": 1, "name": "Conta Corrente", "balance": 5000.00},
        {"id": 2, "name": "Poupança", "balance": 10000.00}
    ]

@app.get("/api/v1/financial/groups")
async def get_groups():
    return [
        {"id": 1, "name": "Receitas", "description": "Grupo de receitas"},
        {"id": 2, "name": "Despesas", "description": "Grupo de despesas"}
    ]

@app.get("/api/v1/financial/account-subgroups")
async def get_subgroups():
    return [
        {"id": 1, "name": "Vendas", "group_id": 1},
        {"id": 2, "name": "Salários", "group_id": 2}
    ]

@app.get("/api/v1/financial/forecasts")
async def get_forecasts():
    return [
        {"id": 1, "account_id": 1, "amount": 5000.00, "description": "Previsão de vendas"}
    ]

@app.get("/api/v1/financial/cash-flow")
async def get_cash_flow():
    return [
        {"date": "2024-01-01", "opening_balance": 10000, "total_revenue": 5000, "total_expenses": 3000, "closing_balance": 12000}
    ]

@app.get("/api/v1/reports/cash-flow")
async def get_cash_flow():
    return {
        "cash_flow": [
            {"month": "Jan", "income": 50000, "expense": 30000, "balance": 20000},
            {"month": "Fev", "income": 60000, "expense": 35000, "balance": 25000}
        ]
    }

# Usuários
@app.get("/api/v1/auth/users")
async def get_users():
    return [
        {
            "id": "1",
            "name": "João Silva",
            "email": "joao@empresa.com",
            "phone": "(11) 99999-9999",
            "role": "admin",
            "status": "active",
            "created_at": "2024-01-15",
            "last_login": "2024-08-07"
        },
        {
            "id": "2",
            "name": "Maria Santos",
            "email": "maria@empresa.com",
            "phone": "(11) 88888-8888",
            "role": "manager",
            "status": "active",
            "created_at": "2024-02-20",
            "last_login": "2024-08-06"
        },
        {
            "id": "3",
            "name": "Pedro Costa",
            "email": "pedro@empresa.com",
            "phone": "(11) 77777-7777",
            "role": "user",
            "status": "inactive",
            "created_at": "2024-03-10",
            "last_login": "2024-07-30"
        }
    ]

@app.post("/api/v1/auth/users")
async def create_user():
    return {
        "id": "4",
        "name": "Novo Usuário",
        "email": "novo@empresa.com",
        "phone": "(11) 66666-6666",
        "role": "user",
        "status": "active",
        "created_at": "2024-08-07",
        "last_login": None
    }

@app.put("/api/v1/auth/users/{user_id}")
async def update_user(user_id: str):
    return {
        "id": user_id,
        "name": "Usuário Atualizado",
        "email": "atualizado@empresa.com",
        "phone": "(11) 55555-5555",
        "role": "manager",
        "status": "active",
        "created_at": "2024-01-15",
        "last_login": "2024-08-07"
    }

@app.delete("/api/v1/auth/users/{user_id}")
async def delete_user(user_id: str):
    return {"message": f"Usuário {user_id} deletado com sucesso"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
