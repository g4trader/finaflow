#!/usr/bin/env python3
"""
Script para executar a migration da tabela dashboard_validation_status.
Pode ser executado manualmente ou no pipeline de deploy.
"""
import os
import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from app.database import engine, SessionLocal

def run_migration():
    """Executa a migration SQL para criar a tabela de status de validação"""
    migration_file = backend_path.parent / "migrations" / "create_dashboard_validation_status_table.sql"
    
    if not migration_file.exists():
        print(f"❌ Arquivo de migration não encontrado: {migration_file}")
        return False
    
    print(f"📄 Lendo migration: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print("🔄 Executando migration...")
    db = SessionLocal()
    try:
        # Executar cada statement separadamente
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for statement in statements:
            if statement:
                try:
                    db.execute(text(statement))
                    db.commit()
                except Exception as e:
                    # Ignorar erros de "já existe" (IF NOT EXISTS)
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"⚠️  Tabela/índice já existe, pulando: {statement[:50]}...")
                    else:
                        print(f"⚠️  Erro ao executar statement: {e}")
                        print(f"   Statement: {statement[:100]}...")
        
        # Verificar se a tabela foi criada
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'dashboard_validation_status'
        """))
        
        if result.fetchone():
            print("✅ Migration executada com sucesso!")
            print("✅ Tabela 'dashboard_validation_status' criada")
            return True
        else:
            print("⚠️  Tabela não encontrada após migration")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

