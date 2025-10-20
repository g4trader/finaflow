#!/usr/bin/env python3
"""
🎯 TESTE ESTRUTURA FRONTEND - SEM LOGIN
Verificar se a página de transações está com a nova estrutura
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# Configurações
FRONTEND_URL = "https://finaflow.vercel.app"

def setup_driver():
    """Configurar driver do Selenium"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def test_transactions_page_structure():
    """Testar estrutura da página de transações"""
    print("🎯 TESTE ESTRUTURA - PÁGINA DE TRANSAÇÕES")
    print("=" * 60)
    
    driver = None
    try:
        driver = setup_driver()
        
        # Testar página /transactions
        print("1️⃣ TESTANDO /transactions...")
        driver.get(f"{FRONTEND_URL}/transactions")
        time.sleep(5)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # Verificar se é a nova estrutura
        new_structure_indicators = [
            "Lançamentos Financeiros",
            "Lançamentos Diários", 
            "Data Movimentação",
            "Valor",
            "Grupo",
            "Subgrupo",
            "Conta",
            "Liquidação",
            "Observações"
        ]
        
        found_indicators = []
        for indicator in new_structure_indicators:
            if indicator in page_source:
                found_indicators.append(indicator)
        
        print(f"   📊 Indicadores encontrados: {len(found_indicators)}/{len(new_structure_indicators)}")
        for indicator in found_indicators:
            print(f"      ✅ {indicator}")
        
        if len(found_indicators) >= 5:
            print("   ✅ NOVA ESTRUTURA DETECTADA!")
            transactions_new = True
        else:
            print("   ❌ Estrutura antiga ainda presente")
            transactions_new = False
        
        # Testar página /lancamentos-diarios
        print("\n2️⃣ TESTANDO /lancamentos-diarios...")
        driver.get(f"{FRONTEND_URL}/lancamentos-diarios")
        time.sleep(5)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        if "Lançamentos Diários" in page_source:
            print("   ✅ PÁGINA LANÇAMENTOS DIÁRIOS FUNCIONANDO!")
            lancamentos_ok = True
        else:
            print("   ❌ Página de lançamentos diários não funcionando")
            lancamentos_ok = False
        
        # Verificar se há botões de ação
        action_buttons = ["Novo Lançamento", "Criar", "Adicionar", "Editar", "Excluir"]
        found_buttons = [btn for btn in action_buttons if btn in page_source]
        
        if found_buttons:
            print(f"   📋 Botões de ação encontrados: {found_buttons}")
        
        # Resultado final
        print("\n" + "=" * 60)
        print("🎯 RESULTADO DO TESTE:")
        print(f"✅ /transactions nova estrutura: {'SIM' if transactions_new else 'NÃO'}")
        print(f"✅ /lancamentos-diarios funcionando: {'SIM' if lancamentos_ok else 'NÃO'}")
        
        if transactions_new and lancamentos_ok:
            print("\n🎉 SISTEMA REFATORADO COM SUCESSO!")
            print("✅ Estrutura espelhando planilha Google Sheets")
            print("✅ Páginas funcionando corretamente")
        elif transactions_new or lancamentos_ok:
            print("\n⚠️ SISTEMA PARCIALMENTE ATUALIZADO")
            print("✅ Algumas páginas funcionando")
        else:
            print("\n❌ SISTEMA AINDA COM ESTRUTURA ANTIGA")
            print("❌ Deploy do Vercel pode não ter processado")
        
        print("=" * 60)
        
        return transactions_new and lancamentos_ok
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()

def test_dashboard_access():
    """Testar acesso ao dashboard"""
    print("\n3️⃣ TESTANDO ACESSO AO DASHBOARD...")
    
    driver = None
    try:
        driver = setup_driver()
        
        driver.get(f"{FRONTEND_URL}/dashboard")
        time.sleep(5)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # Verificar se há elementos do dashboard
        dashboard_indicators = ["Dashboard", "Receitas", "Despesas", "Saldo", "Fluxo"]
        found_dashboard = [ind for ind in dashboard_indicators if ind in page_source]
        
        if found_dashboard:
            print(f"   ✅ Elementos do dashboard encontrados: {found_dashboard}")
            return True
        else:
            print("   ❌ Dashboard não carregou corretamente")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar dashboard: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_transactions_page_structure()
    dashboard_ok = test_dashboard_access()
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"✅ Estrutura refatorada: {'SIM' if success else 'NÃO'}")
    print(f"✅ Dashboard acessível: {'SIM' if dashboard_ok else 'NÃO'}")
    
    if success:
        print("\n🎯 SISTEMA PRONTO PARA USO!")
        print("🌐 Acesse: https://finaflow.vercel.app/transactions")
    else:
        print("\n⏳ AGUARDANDO DEPLOY DO VERCEL...")
        print("🔄 O Vercel ainda está processando as atualizações")
