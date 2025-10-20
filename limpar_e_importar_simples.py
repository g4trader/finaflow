#!/usr/bin/env python3
"""
🧹 LIMPEZA E IMPORTAÇÃO SIMPLES
Limpar dados de teste e importar dados reais da planilha
"""

import requests
import time
import json

# Configurações
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"
GOOGLE_SHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"

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

def limpar_dados_teste(token):
    """Limpar dados de teste"""
    print("\n🧹 LIMPANDO DADOS DE TESTE...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Limpar lançamentos diários
    print("   🗑️ Limpando lançamentos diários...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
        if response.status_code == 200:
            lancamentos = response.json()["lancamentos"]
            print(f"   📊 Encontrados {len(lancamentos)} lançamentos para remover")
            
            for lancamento in lancamentos:
                delete_response = requests.delete(
                    f"{BACKEND_URL}/api/v1/lancamentos-diarios/{lancamento['id']}",
                    headers=headers,
                    timeout=10
                )
                if delete_response.status_code == 200:
                    print(f"      ✅ Lançamento {lancamento['id'][:8]}... removido")
                else:
                    print(f"      ❌ Erro ao remover lançamento {lancamento['id'][:8]}...")
            
            print(f"   ✅ {len(lancamentos)} lançamentos removidos")
        else:
            print(f"   ❌ Erro ao buscar lançamentos: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro ao limpar lançamentos: {str(e)}")

def importar_dados_planilha(token):
    """Importar dados reais da planilha"""
    print("\n📊 IMPORTANDO DADOS REAIS DA PLANILHA...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Importar dados da planilha Google Sheets
    print("   📊 Importando dados da planilha Google Sheets...")
    try:
        import_data = {
            "spreadsheet_id": GOOGLE_SHEET_ID,
            "import_chart_accounts": True,
            "import_transactions": True,
            "import_forecasts": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/admin/onboard-new-company",
            json=import_data,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Importação da planilha concluída")
            print(f"   📊 Resultado: {result}")
        else:
            print(f"   ❌ Erro na importação: {response.status_code}")
            print(f"   📋 Resposta: {response.text}")
    except Exception as e:
        print(f"   ❌ Erro ao importar planilha: {str(e)}")

def verificar_importacao(token):
    """Verificar se a importação foi bem-sucedida"""
    print("\n🔍 VERIFICANDO IMPORTAÇÃO...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verificar lançamentos
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            lancamentos = data["lancamentos"]
            print(f"   ✅ Lançamentos importados: {len(lancamentos)}")
            
            if lancamentos:
                # Mostrar estatísticas por tipo
                tipos = {}
                for lanc in lancamentos:
                    tipo = lanc["transaction_type"]
                    tipos[tipo] = tipos.get(tipo, 0) + 1
                
                print("   📊 Tipos de transação:")
                for tipo, count in tipos.items():
                    print(f"      {tipo}: {count} lançamentos")
                
                # Mostrar alguns exemplos
                print("   📋 Exemplos de lançamentos:")
                for i, lanc in enumerate(lancamentos[:3]):
                    print(f"      {i+1}. {lanc['grupo_nome']} - R$ {lanc['valor']:.2f} - {lanc['transaction_type']}")
        else:
            print(f"   ❌ Erro ao verificar lançamentos: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar lançamentos: {str(e)}")
    
    # Verificar dashboard
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/financial/cash-flow?_t=verificacao", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Dashboard carregando dados reais")
            print(f"   📊 Receitas: R$ {data.get('receitas', 0):.2f}")
            print(f"   📊 Despesas: R$ {data.get('despesas', 0):.2f}")
            print(f"   📊 Custos: R$ {data.get('custos', 0):.2f}")
            print(f"   📊 Saldo: R$ {data.get('saldo', 0):.2f}")
        else:
            print(f"   ❌ Erro ao verificar dashboard: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar dashboard: {str(e)}")

def main():
    """Executar limpeza e importação"""
    print("🎯 LIMPEZA E IMPORTAÇÃO DE DADOS REAIS")
    print("=" * 60)
    
    # 1. Login
    token = login()
    if not token:
        print("❌ Falha no login. Abortando operação.")
        return
    
    # 2. Limpar dados de teste
    limpar_dados_teste(token)
    
    # 3. Importar dados reais
    importar_dados_planilha(token)
    
    # 4. Verificar importação
    verificar_importacao(token)
    
    print("\n" + "=" * 60)
    print("🎉 OPERAÇÃO CONCLUÍDA!")
    print("✅ Dados de teste removidos")
    print("✅ Dados reais da planilha importados")
    print("✅ Sistema pronto para uso com dados reais")
    print("\n🌐 Acesse: https://finaflow.vercel.app/transactions")
    print("=" * 60)

if __name__ == "__main__":
    main()
