#!/usr/bin/env python3
"""
Script para corrigir diretamente a coluna transaction_type no banco
"""

import psycopg2
import os
from urllib.parse import urlparse

# Configurações do banco
DATABASE_URL = "postgresql://finaflow_user:finaflow_password@34.28.5.106:5432/finaflow_db"

def fix_transaction_type_column():
    """Corrigir coluna transaction_type para permitir NULL"""
    print("🔧 Conectando ao banco de dados...")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ Conectado ao banco de dados")
        
        # Verificar se a coluna já permite NULL
        cursor.execute("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'lancamentos_diarios' 
            AND column_name = 'transaction_type'
        """)
        
        result = cursor.fetchone()
        if result:
            is_nullable = result[0]
            print(f"📊 Status atual da coluna transaction_type: is_nullable = {is_nullable}")
            
            if is_nullable == 'YES':
                print("✅ Coluna já permite valores NULL")
                return True
        
        # Alterar coluna para permitir NULL
        print("🔧 Alterando coluna transaction_type para permitir NULL...")
        cursor.execute("""
            ALTER TABLE lancamentos_diarios 
            ALTER COLUMN transaction_type DROP NOT NULL
        """)
        
        conn.commit()
        print("✅ Coluna transaction_type agora permite valores NULL")
        
        # Verificar novamente
        cursor.execute("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'lancamentos_diarios' 
            AND column_name = 'transaction_type'
        """)
        
        result = cursor.fetchone()
        if result:
            is_nullable = result[0]
            print(f"📊 Novo status da coluna transaction_type: is_nullable = {is_nullable}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir coluna: {str(e)}")
        return False

def main():
    """Função principal"""
    print("🚀 Corrigindo coluna transaction_type no banco de dados")
    print("=" * 60)
    
    if fix_transaction_type_column():
        print("\n🎉 Correção realizada com sucesso!")
        print("📊 Agora você pode executar a reimportação dos lançamentos diários.")
    else:
        print("\n❌ Falha na correção da coluna.")

if __name__ == "__main__":
    main()
