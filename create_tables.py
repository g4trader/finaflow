#!/usr/bin/env python3
"""
Script simples para criar apenas as tabelas
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Forçar uso do PostgreSQL
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db"

from app.database import engine
from app.models.auth import Base

def create_tables():
    """Cria apenas as tabelas"""
    print("🔄 Criando tabelas...")
    
    try:
        # Criar todas as tabelas
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso")
        
        # Verificar se as tabelas foram criadas
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = result.fetchall()
            print(f"📋 Tabelas criadas: {[table[0] for table in tables]}")
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()
