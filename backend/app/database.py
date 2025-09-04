from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from typing import Generator

# Configuração do banco de dados - APENAS PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db"  # PostgreSQL padrão
)

# Verificar se está usando PostgreSQL
if not DATABASE_URL.startswith("postgresql"):
    raise ValueError("APENAS PostgreSQL é suportado. Configure DATABASE_URL para PostgreSQL.")

print(f"🔗 Conectando ao banco: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'PostgreSQL'}")

# Configuração para PostgreSQL
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Configuração da sessão
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para os modelos
Base = declarative_base()

def get_db() -> Generator:
    """
    Dependency para obter sessão do banco de dados.
    Gerencia automaticamente o fechamento da sessão.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Cria todas as tabelas no banco de dados PostgreSQL.
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Remove todas as tabelas do banco de dados PostgreSQL.
    """
    Base.metadata.drop_all(bind=engine)
