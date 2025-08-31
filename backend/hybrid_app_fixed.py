from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
import jwt
import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Importar configurações do banco de dados
from app.database import get_db, engine
from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess, Base as AuthBase
from app.models.chart_of_accounts import (
    AccountGroup, AccountSubgroup, Account,
    AccountGroupCreate, AccountGroupUpdate, AccountGroupResponse,
    AccountSubgroupCreate, AccountSubgroupUpdate, AccountSubgroupResponse,
    AccountCreate, AccountUpdate, AccountResponse
)

# Criar aplicação FastAPI
app = FastAPI(title="FinaFlow Backend", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar autenticação
security = HTTPBearer()

# Função para obter usuário atual
def get_current_user(credentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoint de teste
@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint para testar conexão com banco de dados
@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        # Testar conexão simples
        from sqlalchemy import text
        result = db.execute(text("SELECT 1"))
        return {"message": "Database connection successful", "result": result.scalar()}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

# Endpoint para criar tabelas
@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import create_tables
        create_tables()
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"message": "Failed to create tables", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting FinaFlow Backend...")
    print("📊 Testing database connection...")
    
    try:
        # Testar conexão com banco de dados
        from app.database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️ Database connection warning: {e}")
        print("🔄 Continuing without database...")
    
    print("🌐 Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)

from fastapi.security import HTTPBearer
import uvicorn
import os
import jwt
import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Importar configurações do banco de dados
from app.database import get_db, engine
from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess, Base as AuthBase
from app.models.chart_of_accounts import (
    AccountGroup, AccountSubgroup, Account,
    AccountGroupCreate, AccountGroupUpdate, AccountGroupResponse,
    AccountSubgroupCreate, AccountSubgroupUpdate, AccountSubgroupResponse,
    AccountCreate, AccountUpdate, AccountResponse
)

# Criar aplicação FastAPI
app = FastAPI(title="FinaFlow Backend", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar autenticação
security = HTTPBearer()

# Função para obter usuário atual
def get_current_user(credentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoint de teste
@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint para testar conexão com banco de dados
@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        # Testar conexão simples
        from sqlalchemy import text
        result = db.execute(text("SELECT 1"))
        return {"message": "Database connection successful", "result": result.scalar()}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

# Endpoint para criar tabelas
@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import create_tables
        create_tables()
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"message": "Failed to create tables", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting FinaFlow Backend...")
    print("📊 Testing database connection...")
    
    try:
        # Testar conexão com banco de dados
        from app.database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️ Database connection warning: {e}")
        print("🔄 Continuing without database...")
    
    print("🌐 Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)

from fastapi.security import HTTPBearer
import uvicorn
import os
import jwt
import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Importar configurações do banco de dados
from app.database import get_db, engine
from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess, Base as AuthBase
from app.models.chart_of_accounts import (
    AccountGroup, AccountSubgroup, Account,
    AccountGroupCreate, AccountGroupUpdate, AccountGroupResponse,
    AccountSubgroupCreate, AccountSubgroupUpdate, AccountSubgroupResponse,
    AccountCreate, AccountUpdate, AccountResponse
)

# Criar aplicação FastAPI
app = FastAPI(title="FinaFlow Backend", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar autenticação
security = HTTPBearer()

# Função para obter usuário atual
def get_current_user(credentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoint de teste
@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint para testar conexão com banco de dados
@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        # Testar conexão simples
        from sqlalchemy import text
        result = db.execute(text("SELECT 1"))
        return {"message": "Database connection successful", "result": result.scalar()}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

# Endpoint para criar tabelas
@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import create_tables
        create_tables()
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"message": "Failed to create tables", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting FinaFlow Backend...")
    print("📊 Testing database connection...")
    
    try:
        # Testar conexão com banco de dados
        from app.database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️ Database connection warning: {e}")
        print("🔄 Continuing without database...")
    
    print("🌐 Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)

from fastapi.security import HTTPBearer
import uvicorn
import os
import jwt
import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Importar configurações do banco de dados
from app.database import get_db, engine
from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess, Base as AuthBase
from app.models.chart_of_accounts import (
    AccountGroup, AccountSubgroup, Account,
    AccountGroupCreate, AccountGroupUpdate, AccountGroupResponse,
    AccountSubgroupCreate, AccountSubgroupUpdate, AccountSubgroupResponse,
    AccountCreate, AccountUpdate, AccountResponse
)

# Criar aplicação FastAPI
app = FastAPI(title="FinaFlow Backend", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar autenticação
security = HTTPBearer()

# Função para obter usuário atual
def get_current_user(credentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoint de teste
@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint para testar conexão com banco de dados
@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        # Testar conexão simples
        from sqlalchemy import text
        result = db.execute(text("SELECT 1"))
        return {"message": "Database connection successful", "result": result.scalar()}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

# Endpoint para criar tabelas
@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import create_tables
        create_tables()
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"message": "Failed to create tables", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting FinaFlow Backend...")
    print("📊 Testing database connection...")
    
    try:
        # Testar conexão com banco de dados
        from app.database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️ Database connection warning: {e}")
        print("🔄 Continuing without database...")
    
    print("🌐 Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)

from fastapi.security import HTTPBearer
import uvicorn
import os
import jwt
import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Importar configurações do banco de dados
from app.database import get_db, engine
from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess, Base as AuthBase
from app.models.chart_of_accounts import (
    AccountGroup, AccountSubgroup, Account,
    AccountGroupCreate, AccountGroupUpdate, AccountGroupResponse,
    AccountSubgroupCreate, AccountSubgroupUpdate, AccountSubgroupResponse,
    AccountCreate, AccountUpdate, AccountResponse
)

# Criar aplicação FastAPI
app = FastAPI(title="FinaFlow Backend", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar autenticação
security = HTTPBearer()

# Função para obter usuário atual
def get_current_user(credentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoint de teste
@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint para testar conexão com banco de dados
@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        # Testar conexão simples
        from sqlalchemy import text
        result = db.execute(text("SELECT 1"))
        return {"message": "Database connection successful", "result": result.scalar()}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

# Endpoint para criar tabelas
@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import create_tables
        create_tables()
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"message": "Failed to create tables", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting FinaFlow Backend...")
    print("📊 Testing database connection...")
    
    try:
        # Testar conexão com banco de dados
        from app.database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️ Database connection warning: {e}")
        print("🔄 Continuing without database...")
    
    print("🌐 Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
