#!/usr/bin/env python3
"""
Script simples para testar conexão com banco de dados
"""

import os
import psycopg2
from sqlalchemy import create_engine, text

# Configurar variável de ambiente
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db"

def test_connection():
    """Testa conexão direta com psycopg2"""
    print("🔌 Testando conexão direta com psycopg2...")
    try:
        conn = psycopg2.connect(
            host="34.70.102.98",
            port="5432",
            database="finaflow_db",
            user="finaflow_user",
            password="finaflow_password"
        )
        print("✅ Conexão direta bem-sucedida!")
        
        # Testar criação de tabela simples
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            )
        """)
        conn.commit()
        print("✅ Tabela de teste criada com sucesso!")
        
        # Verificar se a tabela foi criada
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        print(f"📋 Tabelas no schema público: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro na conexão direta: {e}")

def test_sqlalchemy():
    """Testa conexão com SQLAlchemy"""
    print("\n🔌 Testando conexão com SQLAlchemy...")
    try:
        engine = create_engine("postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db")
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ Conexão SQLAlchemy bem-sucedida! PostgreSQL version: {version[0]}")
            
            # Testar criação de tabela
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_sqlalchemy (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100)
                )
            """))
            conn.commit()
            print("✅ Tabela SQLAlchemy criada com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro na conexão SQLAlchemy: {e}")

if __name__ == "__main__":
    test_connection()
    test_sqlalchemy()
