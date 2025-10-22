#!/usr/bin/env python3
"""
Script para forçar a correção da coluna transaction_type
"""

import requests
import json

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
USERNAME = "lucianoterresrosa"
PASSWORD = "xs95LIa9ZduX"

def fazer_login():
    """Fazer login no sistema"""
    print("🔐 Fazendo login...")
    
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print("✅ Login realizado com sucesso")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None

def forcar_correcao_coluna(token):
    """Forçar correção da coluna transaction_type"""
    print("🔧 Forçando correção da coluna transaction_type...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Primeiro, tentar limpar (que deve corrigir a coluna)
    response = requests.post(
        f"{BACKEND_URL}/api/v1/admin/limpar-via-sql", 
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Limpeza executada: {data.get('message', 'Sucesso')}")
        
        # Verificar se a coluna foi corrigida
        column_fixed = data.get('column_fixed', False)
        message = data.get('message', '')
        
        if column_fixed or 'corrigida' in message.lower():
            print("✅ Coluna transaction_type foi corrigida!")
            return True
        else:
            print("⚠️ Coluna pode não ter sido corrigida")
            return False
    else:
        print(f"❌ Erro na limpeza: {response.status_code} - {response.text}")
        return False

def testar_importacao_simples(token):
    """Testar importação de um lançamento simples"""
    print("🧪 Testando importação de lançamento simples...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Dados de teste
    test_data = {
        "data_movimentacao": "2025-01-01",
        "valor": 100.00,
        "observacoes": "Teste de importação",
        "conta_id": "eb91042e-83eb-4251-9fba-f8b382fcddec",  # ID de uma conta existente
        "subgrupo_id": "9bbc2e28-6cd8-4b35-a3b5-92b81226f0fd",  # ID de um subgrupo existente
        "grupo_id": "61366662-e85d-40c1-93d4-efe172beb137",  # ID de um grupo existente
        "transaction_type": None  # Testar com NULL
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/lancamentos-diarios", 
        headers=headers,
        json=test_data
    )
    
    if response.status_code == 200:
        print("✅ Teste de importação com transaction_type=NULL funcionou!")
        return True
    else:
        print(f"❌ Teste de importação falhou: {response.status_code} - {response.text}")
        return False

def main():
    """Função principal"""
    print("🚀 Forçando correção da coluna transaction_type")
    print("=" * 60)
    
    # 1. Login
    token = fazer_login()
    if not token:
        print("❌ Falha no login. Abortando.")
        return
    
    # 2. Forçar correção da coluna
    if not forcar_correcao_coluna(token):
        print("❌ Falha na correção da coluna.")
        return
    
    # 3. Testar importação simples
    if testar_importacao_simples(token):
        print("\n🎉 Correção bem-sucedida!")
        print("📊 Agora você pode executar a reimportação completa.")
    else:
        print("\n❌ Correção não funcionou. A coluna ainda não permite NULL.")

if __name__ == "__main__":
    main()
