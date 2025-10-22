#!/usr/bin/env python3
"""
📊 IMPORTAÇÃO VIA CSV (ALTERNATIVA)
Importar dados usando o endpoint de CSV que não depende do Google Sheets API
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

def verificar_estado_atual(headers):
    """Verificar estado atual dos dados"""
    print("\n📋 ESTADO ATUAL DOS DADOS:")
    print("-" * 40)
    
    try:
        # Verificar lançamentos
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios?limit=1", headers=headers, timeout=30)
        if response.status_code == 200:
            total_lancamentos = response.json().get("total", 0)
            print(f"   📊 Lançamentos diários: {total_lancamentos}")
        else:
            print(f"   ❌ Erro ao verificar lançamentos: {response.status_code}")
        
        # Verificar plano de contas
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios/plano-contas", headers=headers, timeout=30)
        if response.status_code == 200:
            plano = response.json()
            grupos = len(plano.get("grupos", []))
            subgrupos = len(plano.get("subgrupos", []))
            contas = len(plano.get("contas", []))
            print(f"   📋 Plano de contas: {grupos} grupos, {subgrupos} subgrupos, {contas} contas")
        else:
            print(f"   ❌ Erro ao verificar plano de contas: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar estado: {e}")

def importar_plano_contas_csv(headers):
    """Importar plano de contas via CSV"""
    print("\n📋 IMPORTANDO PLANO DE CONTAS VIA CSV...")
    print("-" * 40)
    
    # CSV do plano de contas (dados da planilha)
    csv_content = """Conta,Subgrupo,Grupo
Diversos,Receita,Receita
Compra de material para consumo-CSP,Custos com Serviços Prestados,Custos
Tarifas Bancárias,Despesas Financeiras,Despesas Operacionais
Aluguel,Despesas Operacionais,Despesas Operacionais
Energia Elétrica,Despesas Operacionais,Despesas Operacionais
Água,Despesas Operacionais,Despesas Operacionais
Internet,Despesas Operacionais,Despesas Operacionais
Telefone,Despesas Operacionais,Despesas Operacionais
Combustível,Despesas Operacionais,Despesas Operacionais
Manutenção de Equipamentos,Despesas Operacionais,Despesas Operacionais
Material de Limpeza,Despesas Operacionais,Despesas Operacionais
Material de Escritório,Despesas Operacionais,Despesas Operacionais
Salários,Despesas Operacionais,Despesas Operacionais
Encargos Sociais,Despesas Operacionais,Despesas Operacionais
Vale Transporte,Despesas Operacionais,Despesas Operacionais
Vale Refeição,Despesas Operacionais,Despesas Operacionais
Seguro,Despesas Operacionais,Despesas Operacionais
Contador,Despesas Operacionais,Despesas Operacionais
Marketing,Despesas Operacionais,Despesas Operacionais
Banco do Brasil,Contas Bancárias,Ativo
Caixa,Caixa,Ativo
Investimentos,Investimentos,Ativo"""
    
    try:
        # Criar arquivo temporário
        files = {
            'file': ('plano_contas.csv', csv_content, 'text/csv')
        }
        
        response = requests.post(f"{BACKEND_URL}/api/v1/chart-accounts/import", 
                               headers=headers, files=files, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Plano de contas importado: {result.get('message', 'Sucesso')}")
            return True
        else:
            print(f"   ❌ Erro ao importar plano de contas: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro na importação do plano de contas: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 IMPORTAÇÃO VIA CSV (ALTERNATIVA)")
    print("=" * 60)
    print(f"👤 Usuário: {CREDENTIALS['username']}")
    print("=" * 60)
    
    # Fazer login
    headers = fazer_login()
    if not headers:
        return
    
    # Verificar estado atual
    verificar_estado_atual(headers)
    
    # Importar plano de contas via CSV
    print("\n🚀 Iniciando importação via CSV...")
    
    sucessos = 0
    
    # 1. Plano de contas
    if importar_plano_contas_csv(headers):
        sucessos += 1
        time.sleep(2)
    
    # Verificar estado final
    print("\n📋 ESTADO FINAL DOS DADOS:")
    print("-" * 40)
    verificar_estado_atual(headers)
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DA IMPORTAÇÃO:")
    print(f"   ✅ Sucessos: {sucessos}/1")
    print(f"   ❌ Falhas: {1 - sucessos}/1")
    
    if sucessos == 1:
        print("\n🎉 IMPORTAÇÃO COMPLETA COM SUCESSO!")
        print("🌐 Acesse: https://finaflow.vercel.app/transactions")
    else:
        print("\n⚠️  IMPORTAÇÃO FALHOU - Verifique os erros acima")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
