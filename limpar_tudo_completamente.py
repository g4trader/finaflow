#!/usr/bin/env python3
"""
🧹 LIMPEZA COMPLETA E DEFINITIVA
Remover TODOS os dados de teste do sistema
"""

import requests
import time
import json

# Configurações
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"

# Credenciais
CREDENTIALS = {
    "username": "lucianoterresrosa",
    "password": "xs95LIa9ZduX"
}

def login():
    """Fazer login no sistema"""
    print("🔐 FAZENDO LOGIN...")
    
    response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=10)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login realizado com sucesso")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code}")
        return None

def limpar_todos_lancamentos(token):
    """Limpar TODOS os lançamentos"""
    print("\n🧹 LIMPANDO TODOS OS LANÇAMENTOS...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Buscar todos os lançamentos
    response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        lancamentos = data["lancamentos"]
        print(f"   📊 Encontrados {len(lancamentos)} lançamentos para remover")
        
        # Remover cada lançamento
        for lancamento in lancamentos:
            print(f"   🗑️ Removendo lançamento: {lancamento['id'][:8]}...")
            print(f"      Data: {lancamento['data_movimentacao'][:10]}")
            print(f"      Valor: R$ {lancamento['valor']}")
            print(f"      Observações: {lancamento.get('observacoes', 'N/A')[:50]}...")
            
            delete_response = requests.delete(
                f"{BACKEND_URL}/api/v1/lancamentos-diarios/{lancamento['id']}",
                headers=headers,
                timeout=10
            )
            
            if delete_response.status_code == 200:
                print(f"      ✅ Lançamento removido com sucesso")
            else:
                print(f"      ❌ Erro ao remover: {delete_response.status_code}")
                print(f"      📋 Resposta: {delete_response.text}")
        
        print(f"   ✅ {len(lancamentos)} lançamentos processados")
    else:
        print(f"   ❌ Erro ao buscar lançamentos: {response.status_code}")

def verificar_limpeza(token):
    """Verificar se a limpeza foi bem-sucedida"""
    print("\n🔍 VERIFICANDO LIMPEZA...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verificar lançamentos
    response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        lancamentos = data["lancamentos"]
        
        if len(lancamentos) == 0:
            print("   ✅ SUCESSO: Nenhum lançamento encontrado")
            print("   ✅ Sistema completamente limpo")
            return True
        else:
            print(f"   ❌ PROBLEMA: Ainda há {len(lancamentos)} lançamentos")
            for lanc in lancamentos:
                print(f"      - {lanc['id'][:8]}... - R$ {lanc['valor']}")
            return False
    else:
        print(f"   ❌ Erro ao verificar: {response.status_code}")
        return False

def verificar_dashboard(token):
    """Verificar dashboard após limpeza"""
    print("\n📊 VERIFICANDO DASHBOARD...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/financial/cash-flow?_t=limpeza", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Dashboard carregado")
            print(f"   📊 Receitas: R$ {data.get('receitas', 0):.2f}")
            print(f"   📊 Despesas: R$ {data.get('despesas', 0):.2f}")
            print(f"   📊 Custos: R$ {data.get('custos', 0):.2f}")
            print(f"   📊 Saldo: R$ {data.get('saldo', 0):.2f}")
            
            if data.get('receitas', 0) == 0 and data.get('despesas', 0) == 0 and data.get('custos', 0) == 0:
                print("   ✅ Dashboard limpo - todos os valores zerados")
            else:
                print("   ⚠️ Dashboard ainda mostra valores")
        else:
            print(f"   ❌ Erro no dashboard: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar dashboard: {str(e)}")

def main():
    """Executar limpeza completa"""
    print("🎯 LIMPEZA COMPLETA E DEFINITIVA")
    print("=" * 60)
    
    # 1. Login
    token = login()
    if not token:
        print("❌ Falha no login. Abortando operação.")
        return
    
    # 2. Limpar todos os lançamentos
    limpar_todos_lancamentos(token)
    
    # 3. Verificar limpeza
    sucesso = verificar_limpeza(token)
    
    # 4. Verificar dashboard
    verificar_dashboard(token)
    
    print("\n" + "=" * 60)
    if sucesso:
        print("🎉 LIMPEZA COMPLETA REALIZADA COM SUCESSO!")
        print("✅ Todos os dados de teste removidos")
        print("✅ Sistema completamente limpo")
        print("✅ Pronto para dados reais")
    else:
        print("❌ PROBLEMA NA LIMPEZA")
        print("⚠️ Ainda há dados no sistema")
        print("🔧 Verificar manualmente")
    
    print("\n🌐 Acesse: https://finaflow.vercel.app/transactions")
    print("=" * 60)

if __name__ == "__main__":
    main()
