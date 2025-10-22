#!/usr/bin/env python3
"""
Script simples para importar dados do Google Sheets
"""

import requests
import json
import time

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
CREDENTIALS = {"username": "lucianoterresrosa", "password": "xs95LIa9ZduX"}

def fazer_login():
    """Fazer login e obter token"""
    print("🔐 Fazendo login...")
    response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=30)
    if response.status_code != 200:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login realizado com sucesso")
    return headers

def importar_plano_contas(headers):
    """Importar plano de contas via CSV"""
    print("\n📊 IMPORTANDO PLANO DE CONTAS...")
    
    # Dados do plano de contas (exemplo)
    plano_contas_data = """Conta,Subgrupo,Grupo,Escolha
Conta Corrente,Bancos,Ativo,Usar
Caixa,Caixa,Ativo,Usar
Vendas,Receitas,Receita,Usar
Fornecedores,Passivo,Passivo,Usar
Salários,Despesas,Despesa,Usar
Aluguel,Despesas,Despesa,Usar
Material de Escritório,Despesas,Despesa,Usar
Equipamentos,Ativo,Ativo,Usar
Capital Social,Patrimônio,Patrimônio,Usar
Lucros Acumulados,Patrimônio,Patrimônio,Usar"""
    
    try:
        # Criar arquivo CSV temporário
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(plano_contas_data)
            temp_file = f.name
        
        # Fazer upload do arquivo
        with open(temp_file, 'rb') as f:
            files = {'file': ('plano_contas.csv', f, 'text/csv')}
            data = {'business_unit_id': '21de180d-8143-4ab3-9c6a-af16a00d13ac'}
            
            response = requests.post(
                f"{BACKEND_URL}/api/v1/financial/chart-accounts/import-csv",
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
        
        # Limpar arquivo temporário
        os.unlink(temp_file)
        
        if response.status_code == 200:
            print("✅ Plano de contas importado com sucesso")
            return True
        else:
            print(f"❌ Erro ao importar plano de contas: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao importar plano de contas: {e}")
        return False

def importar_lancamentos(headers):
    """Importar lançamentos diários via CSV"""
    print("\n💰 IMPORTANDO LANÇAMENTOS DIÁRIOS...")
    
    # Dados de exemplo de lançamentos
    lancamentos_data = """Data,Descrição,Conta,Valor,Tipo
01/01/2025,Recebimento de cliente,Conta Corrente,1000.00,RECEITA
02/01/2025,Pagamento de fornecedor,Conta Corrente,-500.00,DESPESA
03/01/2025,Salário funcionário,Caixa,-2000.00,DESPESA
04/01/2025,Venda de produto,Conta Corrente,1500.00,RECEITA
05/01/2025,Aluguel,Conta Corrente,-800.00,DESPESA"""
    
    try:
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(lancamentos_data)
            temp_file = f.name
        
        with open(temp_file, 'rb') as f:
            files = {'file': ('lancamentos.csv', f, 'text/csv')}
            data = {'business_unit_id': '21de180d-8143-4ab3-9c6a-af16a00d13ac'}
            
            response = requests.post(
                f"{BACKEND_URL}/api/v1/financial/transactions/import-csv",
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
        
        os.unlink(temp_file)
        
        if response.status_code == 200:
            print("✅ Lançamentos importados com sucesso")
            return True
        else:
            print(f"❌ Erro ao importar lançamentos: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao importar lançamentos: {e}")
        return False

def verificar_dados(headers):
    """Verificar se os dados foram importados"""
    print("\n🔍 VERIFICANDO DADOS IMPORTADOS...")
    
    try:
        # Verificar lançamentos
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios?limit=5", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            print(f"   📊 Lançamentos diários: {total}")
        else:
            print(f"   ❌ Erro ao verificar lançamentos: {response.status_code}")
        
        # Verificar saldo disponível
        response = requests.get(f"{BACKEND_URL}/api/v1/saldo-disponivel", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            saldo = data.get("saldo_disponivel", {})
            total = saldo.get("total_geral", 0)
            print(f"   💰 Saldo disponível: R$ {total:,.2f}")
        else:
            print(f"   ❌ Erro ao verificar saldo: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar dados: {e}")

def main():
    """Função principal"""
    print("🚀 IMPORTAÇÃO SIMPLES DE DADOS")
    print("=" * 50)
    
    # Login
    headers = fazer_login()
    if not headers:
        return False
    
    # Importar dados
    sucessos = 0
    
    if importar_plano_contas(headers):
        sucessos += 1
    
    time.sleep(2)  # Aguardar um pouco
    
    if importar_lancamentos(headers):
        sucessos += 1
    
    # Verificar dados
    verificar_dados(headers)
    
    print(f"\n🎉 IMPORTAÇÃO CONCLUÍDA!")
    print(f"   ✅ Sucessos: {sucessos}/2")
    print("🌐 Acesse: https://finaflow.vercel.app/dashboard")
    
    return sucessos == 2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

