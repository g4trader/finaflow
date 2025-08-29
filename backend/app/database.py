from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from typing import Generator

# Configuração do banco de dados
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://finaflow:password@localhost:5432/finaflow"
)

# Configurações do engine para performance e conexões
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Número de conexões no pool
    max_overflow=30,  # Conexões adicionais quando necessário
    pool_pre_ping=True,  # Verificar conexões antes de usar
    pool_recycle=3600,  # Reciclar conexões a cada hora
    echo=False  # Log de SQL (False em produção)
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
    Cria todas as tabelas no banco de dados.
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Remove todas as tabelas do banco de dados.
    """
    Base.metadata.drop_all(bind=engine)
