#!/usr/bin/env python3
"""
🎯 TESTE VISUAL COMPLETO COM SELENIUM
Sistema Lançamentos Diários - Espelhando Planilha Google Sheets
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json

# Configurações
FRONTEND_URL = "https://finaflow.vercel.app"
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"

# Credenciais - Vou testar com superadmin primeiro
CREDENTIALS = {
    "username": "superadmin",
    "password": "Admin@123"
}

def setup_driver():
    """Configurar driver do Selenium"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executar sem interface gráfica
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def test_backend_health():
    """Testar se o backend está funcionando"""
    print("🔍 TESTANDO BACKEND...")
    try:
        # Testar endpoint de login para verificar se backend está online
        response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", 
                               data={"username": "test", "password": "test"}, 
                               timeout=10)
        if response.status_code in [200, 401, 422]:  # Qualquer resposta indica que está online
            print("✅ Backend online")
            return True
        else:
            print(f"❌ Backend com problema: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar backend: {str(e)}")
        return False

def test_frontend_access(driver):
    """Testar acesso ao frontend"""
    print("🔍 TESTANDO FRONTEND...")
    try:
        driver.get(FRONTEND_URL)
        time.sleep(3)
        
        # Verificar se a página carregou
        title = driver.title
        page_source = driver.page_source
        
        print(f"   📋 Título: {title}")
        print(f"   📋 URL: {driver.current_url}")
        
        if "FinaFlow" in title or "Login" in page_source or "finaFlow" in title:
            print("✅ Frontend acessível")
            return True
        else:
            print(f"❌ Frontend com problema: {title}")
            return False
    except Exception as e:
        print(f"❌ Erro ao acessar frontend: {str(e)}")
        return False

def test_login(driver):
    """Testar login no sistema"""
    print("🔍 TESTANDO LOGIN...")
    try:
        # Navegar para página de login
        driver.get(f"{FRONTEND_URL}/login")
        time.sleep(3)
        
        print(f"   📋 URL atual: {driver.current_url}")
        print(f"   📋 Página carregada: {driver.title}")
        
        # Verificar se há campos de login
        try:
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "password")
            print("✅ Campos de login encontrados")
        except NoSuchElementException:
            print("❌ Campos de login não encontrados")
            print(f"   📋 Conteúdo da página: {driver.page_source[:500]}...")
            return False
        
        # Preencher formulário de login
        username_field.clear()
        username_field.send_keys(CREDENTIALS["username"])
        
        password_field.clear()
        password_field.send_keys(CREDENTIALS["password"])
        
        print(f"   📋 Username preenchido: {CREDENTIALS['username']}")
        
        # Clicar no botão de login
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        print("   📋 Botão de login clicado")
        
        # Aguardar redirecionamento
        time.sleep(5)
        
        # Verificar se login foi bem-sucedido
        current_url = driver.current_url
        print(f"   📋 URL após login: {current_url}")
        
        if "/dashboard" in current_url or "/select-business-unit" in current_url:
            print("✅ Login realizado com sucesso")
            return True
        else:
            print(f"❌ Login falhou. URL atual: {current_url}")
            # Verificar se há mensagem de erro
            page_source = driver.page_source
            if "erro" in page_source.lower() or "error" in page_source.lower():
                print("   📋 Possível erro detectado na página")
            return False
            
    except Exception as e:
        print(f"❌ Erro no login: {str(e)}")
        return False

def test_business_unit_selection(driver):
    """Testar seleção de business unit"""
    print("🔍 TESTANDO SELEÇÃO DE BUSINESS UNIT...")
    try:
        # Verificar se está na página de seleção de BU
        if "/select-business-unit" in driver.current_url:
            # Selecionar primeiro business unit disponível
            bu_select = Select(driver.find_element(By.NAME, "business_unit_id"))
            bu_select.select_by_index(1)  # Selecionar primeira opção
            
            # Clicar em continuar
            continue_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            continue_button.click()
            
            time.sleep(3)
            
            # Verificar se foi redirecionado para dashboard
            if "/dashboard" in driver.current_url:
                print("✅ Business Unit selecionado com sucesso")
                return True
            else:
                print(f"❌ Seleção de BU falhou. URL: {driver.current_url}")
                return False
        else:
            print("✅ Já está no dashboard")
            return True
            
    except Exception as e:
        print(f"❌ Erro na seleção de BU: {str(e)}")
        return False

def test_transactions_page(driver):
    """Testar página de transações"""
    print("🔍 TESTANDO PÁGINA DE TRANSAÇÕES...")
    try:
        # Navegar para página de transações
        driver.get(f"{FRONTEND_URL}/transactions")
        time.sleep(5)
        
        # Verificar se a página carregou
        page_source = driver.page_source
        
        # Verificar se é a nova estrutura
        if "Lançamentos Financeiros" in page_source or "Lançamentos Diários" in page_source:
            print("✅ Nova estrutura de transações detectada")
            
            # Verificar campos obrigatórios da planilha
            required_fields = [
                "Data Movimentação",
                "Valor", 
                "Grupo",
                "Subgrupo", 
                "Conta",
                "Liquidação",
                "Observações"
            ]
            
            found_fields = []
            for field in required_fields:
                if field in page_source:
                    found_fields.append(field)
            
            print(f"✅ Campos da planilha encontrados: {len(found_fields)}/{len(required_fields)}")
            for field in found_fields:
                print(f"   📋 {field}")
            
            if len(found_fields) >= 5:  # Pelo menos 5 campos principais
                print("✅ Estrutura espelhando planilha corretamente")
                return True
            else:
                print("❌ Estrutura não espelha planilha")
                return False
                
        else:
            print("❌ Ainda mostra estrutura antiga")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar página de transações: {str(e)}")
        return False

def test_lancamentos_diarios_page(driver):
    """Testar página de lançamentos diários"""
    print("🔍 TESTANDO PÁGINA DE LANÇAMENTOS DIÁRIOS...")
    try:
        # Navegar para página de lançamentos diários
        driver.get(f"{FRONTEND_URL}/lancamentos-diarios")
        time.sleep(5)
        
        # Verificar se a página carregou
        page_source = driver.page_source
        
        if "Lançamentos Diários" in page_source:
            print("✅ Página de lançamentos diários funcionando")
            
            # Verificar se há botão de criar novo lançamento
            if "Novo Lançamento" in page_source or "Criar" in page_source:
                print("✅ Botão de criar lançamento encontrado")
            
            # Verificar se há tabela de lançamentos
            if "table" in page_source.lower():
                print("✅ Tabela de lançamentos encontrada")
            
            return True
        else:
            print("❌ Página de lançamentos diários não funcionando")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar página de lançamentos diários: {str(e)}")
        return False

def test_dashboard(driver):
    """Testar dashboard"""
    print("🔍 TESTANDO DASHBOARD...")
    try:
        # Navegar para dashboard
        driver.get(f"{FRONTEND_URL}/dashboard")
        time.sleep(5)
        
        # Verificar se carregou dados reais
        page_source = driver.page_source
        
        # Verificar se há métricas financeiras
        financial_indicators = ["R$", "Receitas", "Despesas", "Saldo", "Fluxo"]
        found_indicators = [ind for ind in financial_indicators if ind in page_source]
        
        if len(found_indicators) >= 2:
            print(f"✅ Dashboard carregando dados financeiros: {found_indicators}")
            return True
        else:
            print("❌ Dashboard não carregando dados financeiros")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar dashboard: {str(e)}")
        return False

def main():
    """Executar teste visual completo"""
    print("🎯 TESTE VISUAL COMPLETO - SELENIUM")
    print("=" * 60)
    
    driver = None
    try:
        # Configurar driver
        driver = setup_driver()
        
        # Teste 1: Backend
        backend_ok = test_backend_health()
        
        # Teste 2: Frontend
        frontend_ok = test_frontend_access(driver)
        
        if not backend_ok or not frontend_ok:
            print("❌ Sistema não está online")
            return
        
        # Teste 3: Login
        login_ok = test_login(driver)
        if not login_ok:
            print("❌ Login falhou")
            return
        
        # Teste 4: Business Unit
        bu_ok = test_business_unit_selection(driver)
        if not bu_ok:
            print("❌ Seleção de BU falhou")
            return
        
        # Teste 5: Página de Transações
        transactions_ok = test_transactions_page(driver)
        
        # Teste 6: Página de Lançamentos Diários
        lancamentos_ok = test_lancamentos_diarios_page(driver)
        
        # Teste 7: Dashboard
        dashboard_ok = test_dashboard(driver)
        
        # Resultado final
        print("\n" + "=" * 60)
        print("🎯 RESULTADO DO TESTE VISUAL:")
        print(f"✅ Backend: {'OK' if backend_ok else 'FALHOU'}")
        print(f"✅ Frontend: {'OK' if frontend_ok else 'FALHOU'}")
        print(f"✅ Login: {'OK' if login_ok else 'FALHOU'}")
        print(f"✅ Business Unit: {'OK' if bu_ok else 'FALHOU'}")
        print(f"✅ Transações: {'OK' if transactions_ok else 'FALHOU'}")
        print(f"✅ Lançamentos Diários: {'OK' if lancamentos_ok else 'FALHOU'}")
        print(f"✅ Dashboard: {'OK' if dashboard_ok else 'FALHOU'}")
        
        total_tests = 7
        passed_tests = sum([backend_ok, frontend_ok, login_ok, bu_ok, transactions_ok, lancamentos_ok, dashboard_ok])
        
        print(f"\n📊 RESULTADO: {passed_tests}/{total_tests} testes passaram")
        
        if passed_tests >= 6:
            print("🎉 SISTEMA FUNCIONANDO CORRETAMENTE!")
        elif passed_tests >= 4:
            print("⚠️ SISTEMA PARCIALMENTE FUNCIONAL")
        else:
            print("❌ SISTEMA COM PROBLEMAS")
            
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro geral no teste: {str(e)}")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
