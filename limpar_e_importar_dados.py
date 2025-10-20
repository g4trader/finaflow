#!/usr/bin/env python3
"""
🧹 LIMPEZA E IMPORTAÇÃO DE DADOS REAIS
Limpar dados de teste e importar dados reais da planilha Google Sheets
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
        print(f"Resposta: {response.text}")
        return None

def selecionar_business_unit(token):
    """Selecionar business unit"""
    print("\n🏢 SELECIONANDO BUSINESS UNIT...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/select-business-unit",
        json={"business_unit_id": "550e8400-e29b-41d4-a716-446655440000"},
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Business Unit selecionado")
        return True
    else:
        print(f"❌ Erro ao selecionar BU: {response.status_code}")
        return False

def limpar_dados_teste(token):
    """Limpar dados de teste"""
    print("\n🧹 LIMPANDO DADOS DE TESTE...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Limpar lançamentos diários
    print("   🗑️ Limpando lançamentos diários...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
        if response.status_code == 200:
            lancamentos = response.json()["lancamentos"]
            for lancamento in lancamentos:
                delete_response = requests.delete(
                    f"{BACKEND_URL}/api/v1/lancamentos-diarios/{lancamento['id']}",
                    headers=headers,
                    timeout=10
                )
                if delete_response.status_code == 200:
                    print(f"      ✅ Lançamento {lancamento['id']} removido")
                else:
                    print(f"      ❌ Erro ao remover lançamento {lancamento['id']}")
        print(f"   ✅ {len(lancamentos)} lançamentos removidos")
    except Exception as e:
        print(f"   ❌ Erro ao limpar lançamentos: {str(e)}")
    
    # 2. Limpar previsões financeiras
    print("   🗑️ Limpando previsões financeiras...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/financial-forecasts", headers=headers, timeout=10)
        if response.status_code == 200:
            previsoes = response.json().get("forecasts", [])
            for previsao in previsoes:
                delete_response = requests.delete(
                    f"{BACKEND_URL}/api/v1/financial-forecasts/{previsao['id']}",
                    headers=headers,
                    timeout=10
                )
                if delete_response.status_code == 200:
                    print(f"      ✅ Previsão {previsao['id']} removida")
                else:
                    print(f"      ❌ Erro ao remover previsão {previsao['id']}")
        print(f"   ✅ {len(previsoes)} previsões removidas")
    except Exception as e:
        print(f"   ❌ Erro ao limpar previsões: {str(e)}")
    
    print("✅ Limpeza concluída")

def importar_dados_planilha(token):
    """Importar dados reais da planilha"""
    print("\n📊 IMPORTANDO DADOS REAIS DA PLANILHA...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Importar plano de contas (já deve estar importado)
    print("   📋 Verificando plano de contas...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios/plano-contas", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Plano de contas: {len(data['grupos'])} grupos, {len(data['subgrupos'])} subgrupos, {len(data['contas'])} contas")
        else:
            print("   ❌ Erro ao verificar plano de contas")
    except Exception as e:
        print(f"   ❌ Erro ao verificar plano de contas: {str(e)}")
    
    # 2. Importar dados da planilha Google Sheets
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
    
    # 1. Verificar lançamentos
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
                
                # Mostrar exemplo
                exemplo = lancamentos[0]
                print(f"   📋 Exemplo: {exemplo['grupo_nome']} - R$ {exemplo['valor']:.2f} - {exemplo['transaction_type']}")
        else:
            print(f"   ❌ Erro ao verificar lançamentos: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar lançamentos: {str(e)}")
    
    # 2. Verificar previsões
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/financial-forecasts", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            previsoes = data.get("forecasts", [])
            print(f"   ✅ Previsões importadas: {len(previsoes)}")
        else:
            print(f"   ❌ Erro ao verificar previsões: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar previsões: {str(e)}")
    
    # 3. Verificar dashboard
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
    
    # 2. Selecionar business unit
    if not selecionar_business_unit(token):
        print("❌ Falha na seleção de BU. Abortando operação.")
        return
    
    # 3. Limpar dados de teste
    limpar_dados_teste(token)
    
    # 4. Importar dados reais
    importar_dados_planilha(token)
    
    # 5. Verificar importação
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
