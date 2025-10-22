#!/usr/bin/env python3
"""
Script para testar os novos endpoints de extrato diário e totalizadores mensais
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

def testar_extrato_contas_bancarias(token):
    """Testar extrato diário de contas bancárias"""
    print("\n📊 Testando extrato diário de contas bancárias...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/contas-bancarias/extrato-diario", 
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"📈 Período: {data.get('periodo', {}).get('inicio', 'N/A')} - {data.get('periodo', {}).get('fim', 'N/A')}")
        print(f"📈 Total de dias: {len(data.get('extrato', []))}")
        
        if data.get('extrato'):
            primeiro_dia = data['extrato'][0]
            print(f"📋 Primeiro dia: {primeiro_dia.get('data', 'N/A')}")
            print(f"📋 Entradas: R$ {primeiro_dia.get('entradas', 0):,.2f}")
            print(f"📋 Saídas: R$ {primeiro_dia.get('saidas', 0):,.2f}")
            print(f"📋 Saldo: R$ {primeiro_dia.get('saldo_dia', 0):,.2f}")
            print(f"📋 Lançamentos: {len(primeiro_dia.get('lancamentos', []))}")
        
        return True
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
        return False

def testar_totalizadores_contas_bancarias(token):
    """Testar totalizadores mensais de contas bancárias"""
    print("\n📊 Testando totalizadores mensais de contas bancárias...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/contas-bancarias/totalizadores-mensais?ano=2025", 
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"📈 Ano: {data.get('ano', 'N/A')}")
        print(f"📈 Total de meses: {len(data.get('totalizadores', []))}")
        
        if data.get('totalizadores'):
            # Mostrar alguns meses
            for i, mes in enumerate(data['totalizadores'][:3]):
                print(f"📋 Mês {mes.get('mes', 'N/A')}: Entradas R$ {mes.get('entradas', 0):,.2f}, Saídas R$ {mes.get('saidas', 0):,.2f}, Saldo R$ {mes.get('saldo_final', 0):,.2f}")
        
        return True
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
        return False

def testar_extrato_caixa(token):
    """Testar extrato diário de caixa"""
    print("\n📊 Testando extrato diário de caixa...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/caixa/extrato-diario", 
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"📈 Período: {data.get('periodo', {}).get('inicio', 'N/A')} - {data.get('periodo', {}).get('fim', 'N/A')}")
        print(f"📈 Total de dias: {len(data.get('extrato', []))}")
        return True
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
        return False

def testar_extrato_investimentos(token):
    """Testar extrato diário de investimentos"""
    print("\n📊 Testando extrato diário de investimentos...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/investimentos/extrato-diario", 
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"📈 Período: {data.get('periodo', {}).get('inicio', 'N/A')} - {data.get('periodo', {}).get('fim', 'N/A')}")
        print(f"📈 Total de investimentos: {len(data.get('extrato', []))}")
        
        if data.get('extrato'):
            primeiro_inv = data['extrato'][0]
            print(f"📋 Primeiro investimento: {primeiro_inv.get('tipo', 'N/A')} - {primeiro_inv.get('instituicao', 'N/A')}")
            print(f"📋 Valor aplicado: R$ {primeiro_inv.get('valor_aplicado', 0):,.2f}")
            print(f"📋 Valor atual: R$ {primeiro_inv.get('valor_atual', 0):,.2f}")
            print(f"📋 Rentabilidade: R$ {primeiro_inv.get('rentabilidade', 0):,.2f}")
        
        return True
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
        return False

def main():
    """Função principal"""
    print("🚀 Testando novos endpoints de extrato diário e totalizadores mensais")
    print("=" * 70)
    
    # 1. Login
    token = fazer_login()
    if not token:
        print("❌ Falha no login. Abortando.")
        return
    
    # 2. Testar endpoints
    sucessos = 0
    total = 4
    
    if testar_extrato_contas_bancarias(token):
        sucessos += 1
    
    if testar_totalizadores_contas_bancarias(token):
        sucessos += 1
    
    if testar_extrato_caixa(token):
        sucessos += 1
    
    if testar_extrato_investimentos(token):
        sucessos += 1
    
    print("\n" + "=" * 70)
    print(f"🎯 TESTE CONCLUÍDO!")
    print(f"✅ Sucessos: {sucessos}/{total}")
    print(f"📊 Taxa de sucesso: {(sucessos/total)*100:.1f}%")
    
    if sucessos == total:
        print("🎉 Todos os endpoints estão funcionando perfeitamente!")
    else:
        print("⚠️ Alguns endpoints precisam de atenção.")

if __name__ == "__main__":
    main()
