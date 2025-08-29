from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from typing import Generator

# Configuração do banco de dados
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./finaflow.db"  # SQLite para desenvolvimento
)

# Configurações do engine para performance e conexões
if DATABASE_URL.startswith("sqlite"):
    # Configuração para SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
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
    Cria todas as tabelas no banco de dados.
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Remove todas as tabelas do banco de dados.
    """
    Base.metadata.drop_all(bind=engine)
