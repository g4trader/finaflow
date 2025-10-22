#!/usr/bin/env python3
"""
📊 CRIAR DADOS DE TESTE
Criar alguns lançamentos de teste para verificar se o sistema está funcionando
"""

import requests
import json
from datetime import datetime, timedelta

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

def criar_lancamento_teste(headers, data_movimentacao, valor, observacoes, conta_nome="Diversos"):
    """Criar um lançamento de teste"""
    try:
        payload = {
            "data_movimentacao": data_movimentacao,
            "valor": valor,
            "observacoes": observacoes,
            "conta_id": "",  # Será preenchido automaticamente
            "subgrupo_id": "",
            "grupo_id": ""
        }
        
        response = requests.post(f"{BACKEND_URL}/api/v1/lancamentos-diarios", 
                               headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Lançamento criado: {observacoes} - R$ {valor}")
            return True
        else:
            print(f"   ❌ Erro ao criar lançamento: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro na criação: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 CRIAR DADOS DE TESTE")
    print("=" * 60)
    print(f"👤 Usuário: {CREDENTIALS['username']}")
    print("=" * 60)
    
    # Fazer login
    headers = fazer_login()
    if not headers:
        return
    
    # Verificar estado atual
    verificar_estado_atual(headers)
    
    # Criar lançamentos de teste
    print("\n📊 CRIANDO LANÇAMENTOS DE TESTE...")
    print("-" * 40)
    
    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)
    
    lancamentos_teste = [
        {
            "data_movimentacao": hoje.strftime("%Y-%m-%d"),
            "valor": 1500.00,
            "observacoes": "Venda de serviços - Teste"
        },
        {
            "data_movimentacao": hoje.strftime("%Y-%m-%d"),
            "valor": -300.00,
            "observacoes": "Compra de material - Teste"
        },
        {
            "data_movimentacao": ontem.strftime("%Y-%m-%d"),
            "valor": 800.00,
            "observacoes": "Receita diversa - Teste"
        },
        {
            "data_movimentacao": ontem.strftime("%Y-%m-%d"),
            "valor": -150.00,
            "observacoes": "Despesa operacional - Teste"
        }
    ]
    
    sucessos = 0
    for lancamento in lancamentos_teste:
        if criar_lancamento_teste(headers, **lancamento):
            sucessos += 1
    
    # Verificar estado final
    print("\n📋 ESTADO FINAL DOS DADOS:")
    print("-" * 40)
    verificar_estado_atual(headers)
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DA CRIAÇÃO:")
    print(f"   ✅ Sucessos: {sucessos}/{len(lancamentos_teste)}")
    print(f"   ❌ Falhas: {len(lancamentos_teste) - sucessos}/{len(lancamentos_teste)}")
    
    if sucessos > 0:
        print("\n🎉 DADOS DE TESTE CRIADOS COM SUCESSO!")
        print("🌐 Acesse: https://finaflow.vercel.app/transactions")
    else:
        print("\n⚠️  FALHA NA CRIAÇÃO - Verifique os erros acima")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
