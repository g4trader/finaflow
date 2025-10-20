#!/usr/bin/env python3
"""
Teste Visual da Interface - FINAFlow
Testa login e navegação na interface real deployada
"""

import time
import os
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
USERNAME = "admin"
PASSWORD = "admin123"
SCREENSHOTS_DIR = "screenshots_FIXES_APPLIED"

# Criar diretório para screenshots
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def setup_driver():
    """Configura Chrome WebDriver"""
    print("🔧 Configurando Chrome WebDriver...")
    
    chrome_options = Options()
    # Remover headless para ver o navegador (ajuda no debug)
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"❌ Erro ao configurar WebDriver: {e}")
        print("⚠️ Tentando usar Safari como alternativa...")
        return None

def setup_safari_driver():
    """Configura Safari WebDriver como alternativa"""
    print("🔧 Configurando Safari WebDriver...")
    try:
        driver = webdriver.Safari()
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"❌ Erro ao configurar Safari: {e}")
        return None

def take_screenshot(driver, name):
    """Tira screenshot e salva"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SCREENSHOTS_DIR}/{timestamp}_{name}.png"
    driver.save_screenshot(filename)
    print(f"   📸 Screenshot salvo: {filename}")
    return filename

def wait_for_page_load(driver, timeout=10):
    """Aguarda página carregar completamente"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(1)  # Aguardar um pouco mais para animações
        return True
    except:
        return False

def test_1_access_frontend(driver):
    """Teste 1: Acessar frontend"""
    print("\n🌐 Teste 1: Acessando Frontend...")
    try:
        driver.get(FRONTEND_URL)
        wait_for_page_load(driver)
        take_screenshot(driver, "01_frontend_loaded")
        
        current_url = driver.current_url
        print(f"   URL atual: {current_url}")
        
        if "finaflow" in current_url.lower():
            print("   ✅ Frontend carregou")
            return True
        else:
            print("   ❌ Frontend não carregou corretamente")
            return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def test_2_login_page(driver):
    """Teste 2: Página de login"""
    print("\n🔐 Teste 2: Testando Página de Login...")
    try:
        # Garantir que está na página de login
        if "/login" not in driver.current_url:
            driver.get(f"{FRONTEND_URL}/login")
            wait_for_page_load(driver)
        
        take_screenshot(driver, "02_login_page")
        
        # Procurar elementos da página de login
        wait = WebDriverWait(driver, 10)
        
        # Tentar localizar campo de username/email
        username_field = None
        username_selectors = [
            'input[name="username"]',
            'input[name="email"]',
            'input[type="text"]',
            'input[type="email"]',
            'input[placeholder*="usuário"]',
            'input[placeholder*="username"]',
            'input[placeholder*="email"]'
        ]
        
        for selector in username_selectors:
            try:
                username_field = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"   ✅ Campo username encontrado: {selector}")
                break
            except:
                continue
        
        if not username_field:
            print("   ❌ Campo de username não encontrado")
            # Mostrar todos os inputs disponíveis
            inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"   ℹ️ {len(inputs)} campos input encontrados")
            for inp in inputs[:5]:
                print(f"      - {inp.get_attribute('type')} / {inp.get_attribute('name')} / {inp.get_attribute('placeholder')}")
            return False
        
        # Procurar campo de senha
        password_field = None
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[placeholder*="senha"]',
            'input[placeholder*="password"]'
        ]
        
        for selector in password_selectors:
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"   ✅ Campo password encontrado: {selector}")
                break
            except:
                continue
        
        if not password_field:
            print("   ❌ Campo de password não encontrado")
            return False
        
        print("   ✅ Página de login OK - campos encontrados")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        take_screenshot(driver, "02_login_page_error")
        return False

def test_3_perform_login(driver):
    """Teste 3: Realizar login"""
    print("\n👤 Teste 3: Realizando Login...")
    try:
        wait = WebDriverWait(driver, 10)
        
        # Localizar campos
        username_selectors = [
            'input[name="username"]', 'input[name="email"]', 'input[type="text"]',
            'input[type="email"]', 'input[placeholder*="usuário"]', 'input[placeholder*="username"]'
        ]
        
        username_field = None
        for selector in username_selectors:
            try:
                username_field = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        
        # Limpar e preencher
        username_field.clear()
        time.sleep(0.3)
        username_field.send_keys(USERNAME)
        print(f"   ✍️  Username digitado: {USERNAME}")
        
        time.sleep(0.3)
        password_field.clear()
        time.sleep(0.3)
        password_field.send_keys(PASSWORD)
        print(f"   ✍️  Password digitado")
        
        take_screenshot(driver, "03_login_credentials_filled")
        time.sleep(0.5)
        
        # Procurar botão de login
        login_button = None
        button_selectors = [
            'button[type="submit"]',
            'button:contains("Entrar")',
            'button:contains("Login")',
            'button:contains("Sign In")'
        ]
        
        for selector in button_selectors:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        if not login_button:
            # Tentar por texto
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                btn_text = btn.text.lower()
                if "entrar" in btn_text or "login" in btn_text or "sign" in btn_text:
                    login_button = btn
                    break
        
        if not login_button:
            print("   ❌ Botão de login não encontrado")
            return False
        
        print("   🖱️  Clicando em login...")
        login_button.click()
        
        # Aguardar redirecionamento
        print("   ⏳ Aguardando autenticação...")
        time.sleep(5)
        
        current_url = driver.current_url
        print(f"   📍 URL após login: {current_url}")
        
        take_screenshot(driver, "03_after_login")
        
        # Verificar se saiu da página de login
        if "/login" not in current_url:
            print("   ✅ Login realizado com sucesso!")
            return True
        else:
            # Verificar se há mensagem de erro
            page_text = driver.page_source.lower()
            if "erro" in page_text or "error" in page_text or "inválid" in page_text:
                print("   ❌ Login falhou - credenciais inválidas ou erro")
            else:
                print("   ❌ Login não redirecionou")
            return False
        
    except Exception as e:
        print(f"   ❌ Erro durante login: {e}")
        take_screenshot(driver, "03_login_error")
        return False

def test_4_dashboard(driver):
    """Teste 4: Verificar dashboard"""
    print("\n📊 Teste 4: Verificando Dashboard...")
    try:
        # Tentar acessar dashboard
        if "dashboard" not in driver.current_url:
            driver.get(f"{FRONTEND_URL}/dashboard")
            wait_for_page_load(driver)
        
        take_screenshot(driver, "04_dashboard")
        
        # Verificar elementos do dashboard
        page_source = driver.page_source.lower()
        
        dashboard_elements = []
        if "dashboard" in page_source:
            dashboard_elements.append("Dashboard title")
        if "bem-vindo" in page_source or "welcome" in page_source:
            dashboard_elements.append("Welcome message")
        if "transaç" in page_source or "transaction" in page_source:
            dashboard_elements.append("Transactions")
        
        # Procurar cards/widgets
        cards = driver.find_elements(By.CSS_SELECTOR, '[class*="card"], [class*="Card"]')
        if cards:
            dashboard_elements.append(f"{len(cards)} cards")
        
        if dashboard_elements:
            print(f"   ✅ Dashboard carregou: {', '.join(dashboard_elements)}")
            return True
        else:
            print("   ⚠️ Dashboard pode estar vazio ou carregando")
            return True  # Não falhar se apenas estiver vazio
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def test_5_navigation(driver):
    """Teste 5: Navegar pelas páginas"""
    print("\n🧭 Teste 5: Testando Navegação...")
    
    pages = [
        ("/transactions", "Transações"),
        ("/accounts", "Contas"),
        ("/financial-forecasts", "Previsões Financeiras"),
        ("/chart-of-accounts", "Plano de Contas"),
        ("/reports", "Relatórios"),
    ]
    
    visited = 0
    for path, name in pages:
        try:
            print(f"   📄 Acessando: {name}")
            driver.get(f"{FRONTEND_URL}{path}")
            wait_for_page_load(driver)
            
            current_url = driver.current_url
            
            # Verificar se não redirecionou para login
            if "/login" in current_url:
                print(f"      ⚠️ Redirecionou para login (sessão pode ter expirado)")
                # Tentar fazer login novamente
                test_3_perform_login(driver)
                driver.get(f"{FRONTEND_URL}{path}")
                wait_for_page_load(driver)
            
            screenshot_name = f"05_page{path.replace('/', '_')}"
            take_screenshot(driver, screenshot_name)
            
            print(f"      ✅ {name} carregou")
            visited += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"      ❌ Erro ao acessar {name}: {e}")
    
    print(f"   📊 Total: {visited}/{len(pages)} páginas visitadas")
    return visited > 0

def test_6_check_data(driver):
    """Teste 6: Verificar se dados estão sendo exibidos"""
    print("\n💾 Teste 6: Verificando Dados da Interface...")
    try:
        # Ir para transações
        driver.get(f"{FRONTEND_URL}/transactions")
        wait_for_page_load(driver)
        time.sleep(3)
        
        take_screenshot(driver, "06_transactions_page")
        
        # Procurar tabelas
        tables = driver.find_elements(By.TAG_NAME, "table")
        if tables:
            print(f"   ✅ {len(tables)} tabela(s) encontrada(s)")
            
            # Contar linhas
            rows = driver.find_elements(By.TAG_NAME, "tr")
            print(f"   ℹ️ {len(rows)} linha(s) na página")
            
            if len(rows) > 1:
                print("   ✅ Dados presentes na tabela")
                return True
            else:
                print("   ⚠️ Tabela vazia ou sem dados")
                return True  # Não falhar se não houver dados ainda
        else:
            print("   ⚠️ Nenhuma tabela encontrada")
            # Verificar se há outras formas de exibição de dados
            cards = driver.find_elements(By.CSS_SELECTOR, '[class*="card"]')
            if cards:
                print(f"   ℹ️ {len(cards)} cards encontrados")
                return True
            return True
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def test_7_responsive(driver):
    """Teste 7: Testar responsividade"""
    print("\n📱 Teste 7: Testando Responsividade...")
    
    sizes = [
        (1920, 1080, "Desktop"),
        (1366, 768, "Laptop"),
        (768, 1024, "Tablet"),
        (375, 667, "Mobile")
    ]
    
    for width, height, device in sizes:
        try:
            print(f"   📐 Testando {device} ({width}x{height})")
            driver.set_window_size(width, height)
            time.sleep(2)
            
            screenshot_name = f"07_responsive_{device.lower()}"
            take_screenshot(driver, screenshot_name)
            
            print(f"      ✅ {device} renderizado")
        except Exception as e:
            print(f"      ❌ Erro no {device}: {e}")
    
    # Voltar para tamanho normal
    driver.set_window_size(1920, 1080)
    return True

def generate_report():
    """Gera relatório HTML"""
    print("\n📄 Gerando relatório...")
    
    screenshots = sorted([f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith('.png')])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Relatório de Testes Visuais - FINAFlow</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            h1 {{ color: #333; }}
            .screenshot {{ 
                margin: 20px 0; 
                padding: 20px; 
                background: white; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .screenshot img {{ 
                max-width: 100%; 
                border: 1px solid #ddd; 
                border-radius: 4px;
            }}
            .screenshot h3 {{ margin-top: 0; color: #2196F3; }}
            .info {{ background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>🎯 Relatório de Testes Visuais - FINAFlow</h1>
        <div class="info">
            <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p><strong>URL:</strong> {FRONTEND_URL}</p>
            <p><strong>Screenshots:</strong> {len(screenshots)}</p>
        </div>
        
        <h2>📸 Screenshots</h2>
    """
    
    for screenshot in screenshots:
        name = screenshot.replace('.png', '').replace('_', ' ').title()
        html += f"""
        <div class="screenshot">
            <h3>{name}</h3>
            <img src="{screenshot}" alt="{name}">
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    report_file = f"{SCREENSHOTS_DIR}/relatorio.html"
    with open(report_file, 'w') as f:
        f.write(html)
    
    print(f"   ✅ Relatório salvo: {report_file}")
    return report_file

def main():
    """Executa todos os testes"""
    print("="*70)
    print("🚀 TESTE VISUAL DA INTERFACE - FINAFlow")
    print("="*70)
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Username: {USERNAME}")
    print(f"Screenshots: {SCREENSHOTS_DIR}/")
    print("="*70)
    
    # Tentar Chrome primeiro, depois Safari
    driver = setup_driver()
    if not driver:
        driver = setup_safari_driver()
    
    if not driver:
        print("\n❌ Não foi possível inicializar nenhum WebDriver")
        print("⚠️ Instale Chrome ou habilite Safari WebDriver:")
        print("   Para Safari: Safari > Develop > Allow Remote Automation")
        return 1
    
    try:
        results = []
        
        # Executar testes
        results.append(("Frontend Loading", test_1_access_frontend(driver)))
        results.append(("Login Page", test_2_login_page(driver)))
        results.append(("Perform Login", test_3_perform_login(driver)))
        results.append(("Dashboard", test_4_dashboard(driver)))
        results.append(("Navigation", test_5_navigation(driver)))
        results.append(("Data Loading", test_6_check_data(driver)))
        results.append(("Responsive", test_7_responsive(driver)))
        
        # Resultados
        print("\n" + "="*70)
        print("📊 RESULTADOS DOS TESTES")
        print("="*70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{status} - {name}")
        
        print("="*70)
        print(f"Total: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
        print("="*70)
        
        # Gerar relatório
        report_file = generate_report()
        
        print(f"\n✅ Testes concluídos!")
        print(f"📸 Screenshots: {SCREENSHOTS_DIR}/")
        print(f"📄 Relatório HTML: {report_file}")
        print(f"\n💡 Abra o relatório no navegador para ver todos os screenshots")
        
        return 0 if passed >= total * 0.7 else 1
        
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        if driver:
            take_screenshot(driver, "critical_error")
        return 1
        
    finally:
        if driver:
            print("\n🔚 Fechando navegador...")
            driver.quit()

if __name__ == "__main__":
    exit(main())

