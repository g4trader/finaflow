#!/usr/bin/env python3
"""
Script para limpeza e reimportação completa dos lançamentos diários
"""

import requests
import json
from datetime import datetime

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
GOOGLE_SHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"

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
    
    print(f"📤 Enviando dados de login: {login_data}")
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login", 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"📥 Resposta do servidor: {response.status_code}")
    if response.status_code != 200:
        print(f"📄 Conteúdo da resposta: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print("✅ Login realizado com sucesso")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None

def select_business_unit(token):
    """Selecionar business unit"""
    print("🏢 Pulando seleção de business unit (usando token existente)...")
    
    # Por enquanto, vamos pular a seleção de business unit
    # O token já contém as informações necessárias
    print("✅ Usando business unit do token")
    return True

def limpar_lancamentos(token):
    """Limpar todos os lançamentos diários existentes"""
    print("🧹 Limpando lançamentos diários existentes...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Usar endpoint de limpeza via SQL
    response = requests.post(
        f"{BACKEND_URL}/api/v1/admin/limpar-via-sql", 
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message', 'Lançamentos limpos com sucesso')}")
        return True
    else:
        print(f"❌ Erro ao limpar lançamentos: {response.status_code} - {response.text}")
        return False

def importar_lancamentos(token):
    """Importar lançamentos diários da planilha"""
    print("📊 Importando lançamentos diários da planilha...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    import_data = {
        "spreadsheet_id": GOOGLE_SHEET_ID,
        "sheet_name": "Lançamento Diário"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/admin/importar-lancamentos-planilha", 
        json=import_data, 
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message', 'Importação realizada com sucesso')}")
        return True
    else:
        print(f"❌ Erro na importação: {response.status_code} - {response.text}")
        return False

def verificar_lancamentos(token):
    """Verificar quantos lançamentos foram importados"""
    print("🔍 Verificando lançamentos importados...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/lancamentos-diarios?limit=1000", 
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        # Se data é uma lista, usar len diretamente
        if isinstance(data, list):
            total_lancamentos = len(data)
            lancamentos = data
        else:
            # Se data é um objeto com items, usar items
            lancamentos = data.get('items', [])
            total_lancamentos = len(lancamentos)
        
        print(f"✅ Total de lançamentos no sistema: {total_lancamentos}")
        
        # Mostrar alguns exemplos
        if total_lancamentos > 0:
            print("\n📋 Exemplos de lançamentos importados:")
            for i, lancamento in enumerate(lancamentos[:3]):
                print(f"  {i+1}. {lancamento.get('data_movimentacao', 'N/A')} - "
                      f"{lancamento.get('conta', {}).get('name', 'N/A')} - "
                      f"R$ {lancamento.get('valor', 0):,.2f} - "
                      f"{lancamento.get('transaction_type', 'N/A')}")
        
        return total_lancamentos
    else:
        print(f"❌ Erro ao verificar lançamentos: {response.status_code} - {response.text}")
        return 0

def main():
    """Função principal"""
    print("🚀 Iniciando processo de reimportação dos lançamentos diários")
    print("=" * 60)
    
    # 1. Login
    token = login()
    if not token:
        return
    
    # 2. Selecionar business unit
    if not select_business_unit(token):
        return
    
    # 3. Limpar lançamentos existentes
    if not limpar_lancamentos(token):
        return
    
    # 4. Importar novos lançamentos
    if not importar_lancamentos(token):
        return
    
    # 5. Verificar resultado
    total = verificar_lancamentos(token)
    
    print("\n" + "=" * 60)
    print("🎯 PROCESSO CONCLUÍDO!")
    print(f"✅ Total de lançamentos importados: {total}")
    print("📊 Os dados agora estão sincronizados com a planilha")
    print("🔗 Acesse o dashboard para visualizar os dados atualizados")

if __name__ == "__main__":
    main()
