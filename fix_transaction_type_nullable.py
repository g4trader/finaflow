#!/usr/bin/env python3
"""
Script para corrigir a coluna transaction_type para permitir valores NULL
"""

import requests

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"

# Credenciais do usuário LLM Lavanderia
CREDENTIALS = {
    "username": "lucianoterresrosa",
    "password": "xs95LIa9ZduX"
}

def login():
    """Fazer login no sistema"""
    print("🔐 Fazendo login...")
    
    login_data = {
        "username": CREDENTIALS["username"],
        "password": CREDENTIALS["password"]
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login", 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print("✅ Login realizado com sucesso")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None

def fix_transaction_type_column(token):
    """Corrigir coluna transaction_type para permitir NULL"""
    print("🔧 Corrigindo coluna transaction_type...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Executar SQL para alterar a coluna
    sql_data = {
        "sql": "ALTER TABLE lancamentos_diarios ALTER COLUMN transaction_type DROP NOT NULL"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/admin/limpar-via-sql", 
        json=sql_data,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message', 'Coluna corrigida com sucesso')}")
        return True
    else:
        print(f"❌ Erro ao corrigir coluna: {response.status_code} - {response.text}")
        return False

def main():
    """Função principal"""
    print("🔧 Corrigindo coluna transaction_type para permitir NULL")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        return
    
    # Corrigir coluna
    if fix_transaction_type_column(token):
        print("\n" + "=" * 60)
        print("✅ CORREÇÃO CONCLUÍDA!")
        print("📊 A coluna transaction_type agora permite valores NULL")
        print("🔄 Execute novamente a reimportação dos lançamentos")
    else:
        print("\n" + "=" * 60)
        print("❌ FALHA NA CORREÇÃO!")

if __name__ == "__main__":
    main()
