#!/usr/bin/env python3
"""
Script para Importar Plano de Contas
Importa o arquivo CSV do plano de contas para o backend FinaFlow
"""

import requests
import sys
import os
from pathlib import Path

# Configurações
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"
USERNAME = "admin"
PASSWORD = "admin123"
CSV_FILE = "csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def login():
    """Faz login e retorna o token JWT"""
    print("🔐 Fazendo login...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data={
                "username": USERNAME,
                "password": PASSWORD
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login bem-sucedido! Token: {token[:50]}...")
            return token
        else:
            print(f"❌ Erro no login: {response.status_code}")
            print(f"Resposta: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)

def get_user_business_units(token):
    """Obtém as business units do usuário"""
    print("\n📋 Obtendo business units...")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/user-business-units",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            bus = response.json()
            print(f"✅ {len(bus)} business unit(s) encontrada(s)")
            if bus:
                bu = bus[0]
                print(f"   - {bu['name']} ({bu['code']}) - Tenant: {bu['tenant_name']}")
                return bu['id'], bu['tenant_id']
            return None, None
        else:
            print(f"⚠️  Não foi possível obter business units: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"⚠️  Erro ao obter business units: {e}")
        return None, None

def select_business_unit(token, bu_id):
    """Seleciona uma business unit e retorna novo token"""
    print(f"\n🎯 Selecionando business unit: {bu_id}...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/select-business-unit",
            json={
                "business_unit_id": bu_id
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            new_token = data.get("access_token")
            user = data.get("user", {})
            print(f"✅ Business unit selecionada!")
            print(f"   - Tenant: {user.get('tenant_name')}")
            print(f"   - BU: {user.get('business_unit_name')}")
            return new_token
        else:
            print(f"⚠️  Não foi possível selecionar business unit: {response.status_code}")
            print(f"Resposta: {response.text}")
            return token  # Retorna o token original
            
    except Exception as e:
        print(f"⚠️  Erro ao selecionar business unit: {e}")
        return token

def import_chart_of_accounts(token, csv_file):
    """Importa o plano de contas do CSV"""
    print(f"\n📊 Importando plano de contas: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo não encontrado: {csv_file}")
        sys.exit(1)
    
    try:
        # Abrir arquivo CSV
        with open(csv_file, 'rb') as f:
            files = {
                'file': (os.path.basename(csv_file), f, 'text/csv')
            }
            
            # Fazer upload
            print("📤 Enviando arquivo...")
            response = requests.post(
                f"{BACKEND_URL}/api/v1/chart-accounts/import",
                files=files,
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=60
            )
            
            print(f"📥 Resposta recebida: HTTP {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"\n✅ SUCESSO! Plano de contas importado!")
                print(f"   Mensagem: {data.get('message', 'OK')}")
                if 'groups_imported' in data:
                    print(f"   - Grupos: {data['groups_imported']}")
                if 'subgroups_imported' in data:
                    print(f"   - Subgrupos: {data['subgroups_imported']}")
                if 'accounts_imported' in data:
                    print(f"   - Contas: {data['accounts_imported']}")
                return True
            else:
                print(f"\n❌ ERRO ao importar!")
                print(f"Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Detalhes: {error_data}")
                    if 'errors' in error_data:
                        print("\nErros encontrados:")
                        for error in error_data['errors'][:10]:  # Mostrar até 10 erros
                            print(f"  - {error}")
                except:
                    print(f"Resposta: {response.text}")
                return False
                
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("=" * 70)
    print("🚀 IMPORTAÇÃO DE PLANO DE CONTAS - FINAFLOW")
    print("=" * 70)
    
    # 1. Login
    token = login()
    
    # 2. Obter business units
    bu_id, tenant_id = get_user_business_units(token)
    
    # 3. Selecionar business unit (se disponível)
    if bu_id:
        token = select_business_unit(token, bu_id)
    
    # 4. Importar plano de contas
    success = import_chart_of_accounts(token, CSV_FILE)
    
    # Resultado final
    print("\n" + "=" * 70)
    if success:
        print("✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("\nVocê pode agora:")
        print("  1. Acessar o sistema: https://finaflow.vercel.app")
        print("  2. Ver o plano de contas importado")
        print("  3. Importar os próximos arquivos CSV (transações, etc)")
    else:
        print("❌ IMPORTAÇÃO FALHOU")
        print("\nVerifique:")
        print("  1. Se o backend está online")
        print("  2. Se você tem permissões adequadas")
        print("  3. Se o formato do CSV está correto")
    print("=" * 70)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

