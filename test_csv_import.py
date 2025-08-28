#!/usr/bin/env python3
"""
Script para testar a funcionalidade de importação CSV
"""

import requests
import json
import io
import csv

# Configurações
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

def login():
    """Faz login e retorna o token"""
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Erro no login: {response.status_code}")
        return None

def create_test_csv(data, filename):
    """Cria um arquivo CSV de teste"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escrever cabeçalhos
    if data:
        writer.writerow(data[0].keys())
        # Escrever dados
        for row in data:
            writer.writerow(row.values())
    
    return output.getvalue()

def test_import_generic(token):
    """Testa importação genérica"""
    print("🧪 Testando importação genérica...")
    
    # Dados de teste simples
    test_data = [
        {"id": "1", "name": "Teste 1", "value": "100"},
        {"id": "2", "name": "Teste 2", "value": "200"}
    ]
    
    csv_content = create_test_csv(test_data, "test_generic.csv")
    
    files = {
        'file': ('test_generic.csv', io.StringIO(csv_content), 'text/csv')
    }
    
    data = {
        'table': 'test_table'
    }
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(f"{BASE_URL}/csv/import-csv", files=files, data=data, headers=headers)
    
    if response.status_code == 201:
        print("✅ Importação genérica realizada com sucesso!")
        print(f"   Resposta: {response.json()}")
    else:
        print(f"❌ Erro na importação genérica: {response.status_code}")
        print(f"   Resposta: {response.text}")


def test_import_accounts(token):
    """Testa importação de contas"""
    print("\n🧪 Testando importação de contas...")
    
    # Dados de teste
    test_data = [
        {"Conta": "Conta Corrente", "Subgrupo": "Bancos", "Saldo": "1000.00", "Descrição": "Conta principal"},
        {"Conta": "Caixa", "Subgrupo": "Caixa", "Saldo": "500.00", "Descrição": "Caixa da empresa"},
        {"Conta": "Poupança", "Subgrupo": "Bancos", "Saldo": "2000.00", "Descrição": "Conta poupança"}
    ]
    
    csv_content = create_test_csv(test_data, "test_accounts.csv")
    
    files = {
        'file': ('test_accounts.csv', io.StringIO(csv_content), 'text/csv')
    }
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(f"{BASE_URL}/csv/import/accounts", files=files, headers=headers)
    
    if response.status_code == 201:
        print("✅ Importação de contas realizada com sucesso!")
        print(f"   Resposta: {response.json()}")
    else:
        print(f"❌ Erro na importação de contas: {response.status_code}")
        print(f"   Resposta: {response.text}")

def test_import_transactions(token):
    """Testa importação de transações"""
    print("\n🧪 Testando importação de transações...")
    
    # Dados de teste
    test_data = [
        {"Data Movimentação": "02/01/2025", "Conta": "Conta Corrente", "Valor": "100.00", "Descrição": "Recebimento"},
        {"Data Movimentação": "03/01/2025", "Conta": "Caixa", "Valor": "-50.00", "Descrição": "Compra material"},
        {"Data Movimentação": "04/01/2025", "Conta": "Conta Corrente", "Valor": "250.00", "Descrição": "Venda"}
    ]
    
    csv_content = create_test_csv(test_data, "test_transactions.csv")
    
    files = {
        'file': ('test_transactions.csv', io.StringIO(csv_content), 'text/csv')
    }
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(f"{BASE_URL}/csv/import/transactions", files=files, headers=headers)
    
    if response.status_code == 201:
        print("✅ Importação de transações realizada com sucesso!")
        print(f"   Resposta: {response.json()}")
    else:
        print(f"❌ Erro na importação de transações: {response.status_code}")
        print(f"   Resposta: {response.text}")

def test_import_plan_accounts(token):
    """Testa importação do plano de contas"""
    print("\n🧪 Testando importação do plano de contas...")
    
    # Dados de teste
    test_data = [
        {"Conta": "Conta Corrente", "Subgrupo": "Bancos", "Grupo": "Ativo", "Escolha": "Usar"},
        {"Conta": "Caixa", "Subgrupo": "Caixa", "Grupo": "Ativo", "Escolha": "Usar"},
        {"Conta": "Vendas", "Subgrupo": "Receitas", "Grupo": "Receita", "Escolha": "Usar"},
        {"Conta": "Fornecedores", "Subgrupo": "Passivo", "Grupo": "Passivo", "Escolha": "Usar"}
    ]
    
    csv_content = create_test_csv(test_data, "test_plan_accounts.csv")
    
    files = {
        'file': ('test_plan_accounts.csv', io.StringIO(csv_content), 'text/csv')
    }
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(f"{BASE_URL}/csv/import/plan-accounts", files=files, headers=headers)
    
    if response.status_code == 201:
        print("✅ Importação do plano de contas realizada com sucesso!")
        print(f"   Resposta: {response.json()}")
    else:
        print(f"❌ Erro na importação do plano de contas: {response.status_code}")
        print(f"   Resposta: {response.text}")

def test_templates(token):
    """Testa download de templates"""
    print("\n🧪 Testando download de templates...")
    
    templates = ['accounts', 'transactions', 'plan-accounts']
    
    for template in templates:
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.get(f"{BASE_URL}/csv/template/{template}", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Template {template} baixado com sucesso!")
            data = response.json()
            print(f"   Filename: {data['filename']}")
            print(f"   Template: {data['template'][:100]}...")
        else:
            print(f"❌ Erro ao baixar template {template}: {response.status_code}")

def main():
    """Função principal"""
    print("🚀 Testando Funcionalidade de Importação CSV\n")
    
    # Fazer login
    print("🔐 Fazendo login...")
    token = login()
    
    if not token:
        print("❌ Falha no login. Verifique as credenciais e se o servidor está rodando.")
        return
    
    print("✅ Login realizado com sucesso!")
    
    # Testar templates
    test_templates(token)
    
    # Testar importações
    test_import_generic(token)
    test_import_accounts(token)
    test_import_transactions(token)
    test_import_plan_accounts(token)
    
    print("\n🎉 Testes concluídos!")
    print("\n📋 Para usar a funcionalidade:")
    print("1. Acesse: http://localhost:3000/csv-import")
    print("2. Selecione o tipo de importação")
    print("3. Baixe o template correspondente")
    print("4. Preencha com seus dados")
    print("5. Faça o upload e importe!")

if __name__ == "__main__":
    main()
