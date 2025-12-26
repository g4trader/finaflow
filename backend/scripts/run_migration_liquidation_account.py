#!/usr/bin/env python3
"""
Script para executar a migration que adiciona liquidation_account_id à tabela lancamentos_diarios.
"""
import os
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from app.database import SessionLocal

def run_migration():
    """Executa a migration SQL"""
    migration_file = backend_path / "migrations" / "add_liquidation_account_id_to_lancamentos_diarios.sql"
    
    if not migration_file.exists():
        print(f"❌ Arquivo de migration não encontrado: {migration_file}")
        return False
    
    print(f"📄 Lendo migration: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print("🔄 Executando migration...")
    db = SessionLocal()
    try:
        # Executar migration
        db.execute(text(migration_sql))
        db.commit()
        
        # Verificar se a coluna foi criada
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'lancamentos_diarios'
            AND column_name = 'liquidation_account_id'
        """))
        
        if result.fetchone():
            print("✅ Migration executada com sucesso!")
            print("✅ Coluna 'liquidation_account_id' adicionada à tabela 'lancamentos_diarios'")
            return True
        else:
            print("⚠️  Coluna não encontrada após migration")
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

