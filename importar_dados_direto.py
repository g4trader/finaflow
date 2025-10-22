#!/usr/bin/env python3
"""
📊 IMPORTAÇÃO DIRETA DE DADOS
Usar o endpoint temporário para importar dados diretamente
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

def limpar_dados(headers):
    """Limpar dados existentes"""
    print("\n🧹 LIMPANDO DADOS EXISTENTES...")
    print("-" * 40)
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/admin/limpar-tudo-tenant", headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Dados limpos: {result.get('message', 'Sucesso')}")
            return True
        else:
            print(f"   ❌ Erro ao limpar dados: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Erro na limpeza: {e}")
        return False

def importar_dados_direto(headers):
    """Importar dados via endpoint direto"""
    print("\n📊 IMPORTANDO DADOS DIRETAMENTE...")
    print("-" * 40)
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/admin/importar-dados-direto", headers=headers, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Dados importados: {result.get('message', 'Sucesso')}")
            return True
        else:
            print(f"   ❌ Erro ao importar dados: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Erro na importação: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 IMPORTAÇÃO DIRETA DE DADOS")
    print("=" * 60)
    print(f"👤 Usuário: {CREDENTIALS['username']}")
    print("=" * 60)
    
    # Fazer login
    headers = fazer_login()
    if not headers:
        return
    
    # Verificar estado atual
    verificar_estado_atual(headers)
    
    # Limpar dados existentes
    if not limpar_dados(headers):
        print("❌ Falha na limpeza, abortando...")
        return
    
    # Importar dados
    print("\n🚀 Iniciando importação direta...")
    
    sucessos = 0
    
    # Importar dados diretamente
    if importar_dados_direto(headers):
        sucessos += 1
    
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
