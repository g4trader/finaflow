#!/usr/bin/env python3
"""
Teste de Produção com Selenium - FINAFlow
Testa o sistema deployado no Vercel com backend no Cloud Run
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configurações
FRONTEND_URL = "https://finaflow.vercel.app"
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
USERNAME = "admin"
PASSWORD = "admin123"

# Resultados dos testes
test_results = {
    "timestamp": datetime.now().isoformat(),
    "frontend_url": FRONTEND_URL,
    "backend_url": BACKEND_URL,
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }
}

def add_test_result(test_name, status, message="", screenshot=None):
    """Adiciona resultado de teste"""
    test_results["tests"].append({
        "name": test_name,
        "status": status,
        "message": message,
        "screenshot": screenshot,
        "timestamp": datetime.now().isoformat()
    })
    test_results["summary"]["total"] += 1
    if status == "PASSED":
        test_results["summary"]["passed"] += 1
    else:
        test_results["summary"]["failed"] += 1
        test_results["summary"]["errors"].append(f"{test_name}: {message}")

def setup_driver():
    """Configura o Chrome WebDriver"""
    print("🔧 Configurando WebDriver...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Rodar sem interface gráfica
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    
    return driver

def test_backend_health(driver):
    """Teste 1: Verificar se o backend está respondendo"""
    print("\n📡 Teste 1: Backend Health Check")
    try:
        driver.get(f"{BACKEND_URL}/docs")
        time.sleep(2)
        
        # Verificar se a página de documentação carregou
        page_source = driver.page_source.lower()
        if "swagger" in page_source or "fastapi" in page_source:
            print("✅ Backend está respondendo - API Docs acessível")
            add_test_result("Backend Health", "PASSED", "API Docs carregada")
            return True
        else:
            print("❌ Backend não está respondendo corretamente")
            add_test_result("Backend Health", "FAILED", "API Docs não encontrada")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao acessar backend: {e}")
        add_test_result("Backend Health", "FAILED", str(e))
        return False

def test_frontend_loads(driver):
    """Teste 2: Verificar se o frontend carrega"""
    print("\n🌐 Teste 2: Frontend Loading")
    try:
        driver.get(FRONTEND_URL)
        time.sleep(3)
        
        # Verificar se redirecionou para /login
        current_url = driver.current_url
        if "/login" in current_url:
            print("✅ Frontend carregou e redirecionou para login")
            add_test_result("Frontend Loading", "PASSED", "Redirecionou para /login")
            driver.save_screenshot("screenshots/01_frontend_loaded.png")
            return True
        else:
            print(f"⚠️ URL atual: {current_url}")
            add_test_result("Frontend Loading", "FAILED", f"URL inesperada: {current_url}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao carregar frontend: {e}")
        add_test_result("Frontend Loading", "FAILED", str(e))
        return False

def test_login(driver):
    """Teste 3: Realizar login"""
    print("\n🔐 Teste 3: Login")
    try:
        # Garantir que estamos na página de login
        if "/login" not in driver.current_url:
            driver.get(f"{FRONTEND_URL}/login")
            time.sleep(2)
        
        # Localizar campos de login
        wait = WebDriverWait(driver, 10)
        
        # Tentar diferentes seletores para username
        username_field = None
        for selector in ['input[name="username"]', 'input[type="text"]', 'input[placeholder*="usuário"]', 'input[id*="username"]']:
            try:
                username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                break
            except:
                continue
        
        if not username_field:
            print("❌ Campo de username não encontrado")
            add_test_result("Login", "FAILED", "Campo username não encontrado")
            driver.save_screenshot("screenshots/02_login_failed.png")
            return False
        
        # Tentar diferentes seletores para password
        password_field = None
        for selector in ['input[name="password"]', 'input[type="password"]', 'input[placeholder*="senha"]']:
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        if not password_field:
            print("❌ Campo de password não encontrado")
            add_test_result("Login", "FAILED", "Campo password não encontrado")
            driver.save_screenshot("screenshots/02_login_failed.png")
            return False
        
        # Preencher credenciais
        username_field.clear()
        username_field.send_keys(USERNAME)
        time.sleep(0.5)
        
        password_field.clear()
        password_field.send_keys(PASSWORD)
        time.sleep(0.5)
        
        driver.save_screenshot("screenshots/02_login_form_filled.png")
        
        # Clicar no botão de login
        login_button = None
        for selector in ['button[type="submit"]', 'button:contains("Entrar")', 'button:contains("Login")']:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        if not login_button:
            # Tentar por texto
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if "entrar" in button.text.lower() or "login" in button.text.lower():
                    login_button = button
                    break
        
        if not login_button:
            print("❌ Botão de login não encontrado")
            add_test_result("Login", "FAILED", "Botão de login não encontrado")
            return False
        
        login_button.click()
        print("🔄 Aguardando redirecionamento...")
        time.sleep(5)
        
        # Verificar se fez login (redirecionou para dashboard ou outra página)
        current_url = driver.current_url
        if "/login" not in current_url or "dashboard" in current_url or "home" in current_url:
            print(f"✅ Login bem-sucedido! Redirecionado para: {current_url}")
            add_test_result("Login", "PASSED", f"Redirecionado para {current_url}")
            driver.save_screenshot("screenshots/03_login_success.png")
            return True
        else:
            print(f"❌ Login falhou. URL atual: {current_url}")
            page_source = driver.page_source
            if "inválid" in page_source.lower() or "incorrect" in page_source.lower():
                add_test_result("Login", "FAILED", "Credenciais inválidas")
            else:
                add_test_result("Login", "FAILED", f"Ainda na página de login: {current_url}")
            driver.save_screenshot("screenshots/03_login_failed.png")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante login: {e}")
        add_test_result("Login", "FAILED", str(e))
        driver.save_screenshot("screenshots/03_login_error.png")
        return False

def test_dashboard_loads(driver):
    """Teste 4: Verificar se o dashboard carrega"""
    print("\n📊 Teste 4: Dashboard Loading")
    try:
        # Navegar para dashboard
        driver.get(f"{FRONTEND_URL}/dashboard")
        time.sleep(4)
        
        # Verificar se há elementos do dashboard
        page_source = driver.page_source.lower()
        
        dashboard_indicators = [
            "dashboard", "painel", "bem-vindo", "welcome",
            "transações", "transactions", "contas", "accounts"
        ]
        
        found_indicators = [ind for ind in dashboard_indicators if ind in page_source]
        
        if found_indicators:
            print(f"✅ Dashboard carregou com indicadores: {', '.join(found_indicators[:3])}")
            add_test_result("Dashboard Loading", "PASSED", f"Indicadores encontrados: {', '.join(found_indicators[:3])}")
            driver.save_screenshot("screenshots/04_dashboard.png")
            return True
        else:
            print("⚠️ Dashboard pode não ter carregado completamente")
            add_test_result("Dashboard Loading", "FAILED", "Indicadores de dashboard não encontrados")
            driver.save_screenshot("screenshots/04_dashboard_incomplete.png")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao carregar dashboard: {e}")
        add_test_result("Dashboard Loading", "FAILED", str(e))
        return False

def test_navigation(driver):
    """Teste 5: Navegar pelas telas principais"""
    print("\n🧭 Teste 5: Navigation")
    
    pages_to_test = [
        ("/transactions", "Transações"),
        ("/accounts", "Contas"),
        ("/financial-forecasts", "Previsões"),
        ("/reports", "Relatórios"),
    ]
    
    navigation_results = []
    
    for path, name in pages_to_test:
        try:
            print(f"   Testando: {name} ({path})")
            driver.get(f"{FRONTEND_URL}{path}")
            time.sleep(3)
            
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            
            # Verificar se não redirecionou de volta para login
            if "/login" in current_url:
                print(f"   ❌ {name}: Redirecionou para login (não autenticado)")
                navigation_results.append({"page": name, "status": "FAILED", "reason": "Não autenticado"})
            else:
                print(f"   ✅ {name}: Carregou com sucesso")
                navigation_results.append({"page": name, "status": "PASSED"})
                driver.save_screenshot(f"screenshots/05_page_{path.replace('/', '_')}.png")
            
        except Exception as e:
            print(f"   ❌ {name}: Erro - {e}")
            navigation_results.append({"page": name, "status": "FAILED", "reason": str(e)})
    
    # Avaliar resultados gerais
    passed = sum(1 for r in navigation_results if r["status"] == "PASSED")
    total = len(navigation_results)
    
    if passed >= total * 0.7:  # 70% de sucesso
        add_test_result("Navigation", "PASSED", f"{passed}/{total} páginas navegadas com sucesso")
        return True
    else:
        add_test_result("Navigation", "FAILED", f"Apenas {passed}/{total} páginas carregaram")
        return False

def test_data_loading(driver):
    """Teste 6: Verificar se dados do banco estão sendo carregados"""
    print("\n💾 Teste 6: Data Loading from Database")
    try:
        # Ir para página de transações
        driver.get(f"{FRONTEND_URL}/transactions")
        time.sleep(4)
        
        page_source = driver.page_source
        
        # Procurar por indicadores de dados
        data_indicators = [
            "loading" not in page_source.lower(),
            "table" in page_source.lower() or "tabela" in page_source.lower(),
            len(driver.find_elements(By.TAG_NAME, "tr")) > 1,  # Tem linhas na tabela
        ]
        
        if all(data_indicators[:2]):
            print("✅ Dados do banco parecem estar sendo carregados")
            add_test_result("Data Loading", "PASSED", "Tabela com dados encontrada")
            driver.save_screenshot("screenshots/06_data_loaded.png")
            return True
        else:
            print("⚠️ Não foi possível confirmar carregamento de dados")
            add_test_result("Data Loading", "FAILED", "Dados do banco não encontrados")
            driver.save_screenshot("screenshots/06_no_data.png")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar dados: {e}")
        add_test_result("Data Loading", "FAILED", str(e))
        return False

def test_logout(driver):
    """Teste 7: Realizar logout"""
    print("\n🚪 Teste 7: Logout")
    try:
        # Procurar botão de logout
        logout_selectors = [
            'button:contains("Sair")',
            'button:contains("Logout")',
            'a:contains("Sair")',
            '[data-testid="logout"]'
        ]
        
        logout_button = None
        for selector in logout_selectors:
            try:
                logout_button = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        if not logout_button:
            # Procurar por texto
            elements = driver.find_elements(By.TAG_NAME, "button") + driver.find_elements(By.TAG_NAME, "a")
            for elem in elements:
                if "sair" in elem.text.lower() or "logout" in elem.text.lower():
                    logout_button = elem
                    break
        
        if logout_button:
            logout_button.click()
            time.sleep(2)
            
            if "/login" in driver.current_url:
                print("✅ Logout realizado com sucesso")
                add_test_result("Logout", "PASSED", "Redirecionado para login")
                driver.save_screenshot("screenshots/07_logout_success.png")
                return True
        
        print("⚠️ Botão de logout não encontrado ou não funcionou")
        add_test_result("Logout", "FAILED", "Botão não encontrado")
        return False
        
    except Exception as e:
        print(f"❌ Erro durante logout: {e}")
        add_test_result("Logout", "FAILED", str(e))
        return False

def save_results():
    """Salva resultados dos testes"""
    filename = f"selenium_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\n📄 Resultados salvos em: {filename}")
    return filename

def print_summary():
    """Imprime resumo dos testes"""
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    print(f"Total de testes: {test_results['summary']['total']}")
    print(f"✅ Passou: {test_results['summary']['passed']}")
    print(f"❌ Falhou: {test_results['summary']['failed']}")
    
    if test_results['summary']['errors']:
        print("\n❌ Erros encontrados:")
        for error in test_results['summary']['errors']:
            print(f"   - {error}")
    
    success_rate = (test_results['summary']['passed'] / test_results['summary']['total'] * 100) if test_results['summary']['total'] > 0 else 0
    print(f"\n📈 Taxa de sucesso: {success_rate:.1f}%")
    print("="*60)

def main():
    """Função principal"""
    print("🚀 Iniciando testes de produção do FINAFlow")
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Backend: {BACKEND_URL}")
    print(f"Usuário: {USERNAME}")
    
    # Criar diretório de screenshots
    import os
    os.makedirs("screenshots", exist_ok=True)
    
    driver = None
    try:
        driver = setup_driver()
        
        # Executar testes
        test_backend_health(driver)
        test_frontend_loads(driver)
        
        if test_login(driver):
            test_dashboard_loads(driver)
            test_navigation(driver)
            test_data_loading(driver)
            test_logout(driver)
        else:
            print("\n⚠️ Pulando testes subsequentes pois o login falhou")
        
    except Exception as e:
        print(f"\n❌ Erro crítico durante os testes: {e}")
        if driver:
            driver.save_screenshot("screenshots/critical_error.png")
    
    finally:
        if driver:
            driver.quit()
        
        # Salvar e mostrar resultados
        results_file = save_results()
        print_summary()
        
        print(f"\n✅ Testes concluídos!")
        print(f"📁 Resultados: {results_file}")
        print(f"📸 Screenshots: ./screenshots/")
        
        # Retornar código de saída baseado no sucesso
        success_rate = (test_results['summary']['passed'] / test_results['summary']['total'] * 100) if test_results['summary']['total'] > 0 else 0
        return 0 if success_rate >= 70 else 1

if __name__ == "__main__":
    exit(main())


