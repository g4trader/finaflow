"""
Teste automatizado de login usando Selenium
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os

def test_login():
    """Testar login no FinaFlow"""
    
    print("🚀 Iniciando teste de login com Selenium...")
    
    # Configurar Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executar sem interface gráfica
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # Inicializar driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        print("🌐 Acessando frontend...")
        driver.get("http://localhost:3000")
        
        # Aguardar carregamento da página
        wait = WebDriverWait(driver, 15)
        
        print("⏳ Aguardando carregamento da página...")
        time.sleep(5)
        
        # Verificar se a página carregou
        try:
            # Tentar encontrar elementos da página de login
            print("🔍 Procurando elementos de login...")
            
            # Aguardar que algum elemento apareça
            wait.until(EC.any_of(
                EC.presence_of_element_located((By.NAME, "username")),
                EC.presence_of_element_located((By.ID, "username")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='usuário']")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='email']")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='login']"))
            ))
            
            print("✅ Elementos de login encontrados!")
            
            # Tentar diferentes seletores para username
            username_selectors = [
                "input[name='username']",
                "input[id='username']",
                "input[type='text']",
                "input[placeholder*='usuário']",
                "input[placeholder*='email']",
                "input[placeholder*='login']"
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Campo username encontrado com seletor: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not username_field:
                print("❌ Campo username não encontrado")
                # Salvar screenshot para debug
                driver.save_screenshot("login_debug.png")
                print("📸 Screenshot salvo como login_debug.png")
                
                # Mostrar HTML da página
                print("📄 HTML da página:")
                print(driver.page_source[:1000])
                return False
            
            # Tentar diferentes seletores para password
            password_selectors = [
                "input[name='password']",
                "input[id='password']",
                "input[type='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Campo password encontrado com seletor: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                print("❌ Campo password não encontrado")
                driver.save_screenshot("password_debug.png")
                return False
            
            # Preencher campos de login
            print("📝 Preenchendo campos de login...")
            username_field.clear()
            username_field.send_keys("admin")
            
            password_field.clear()
            password_field.send_keys("admin123")
            
            # Procurar botão de submit
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Entrar')",
                "button:contains('Login')",
                "button:contains('Sign in')",
                ".btn-primary",
                ".login-button"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if ":contains(" in selector:
                        # Para seletores com texto, usar XPath
                        xpath = f"//button[contains(text(), '{selector.split(':contains(')[1].split(')')[0]}')]"
                        submit_button = driver.find_element(By.XPATH, xpath)
                    else:
                        submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Botão submit encontrado com seletor: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not submit_button:
                print("❌ Botão de submit não encontrado")
                driver.save_screenshot("submit_debug.png")
                return False
            
            # Clicar no botão de submit
            print("🖱️ Clicando no botão de login...")
            submit_button.click()
            
            # Aguardar redirecionamento ou resposta
            print("⏳ Aguardando resposta do login...")
            time.sleep(5)
            
            # Verificar se o login foi bem-sucedido
            current_url = driver.current_url
            print(f"🔗 URL atual: {current_url}")
            
            # Verificar se há elementos que indicam sucesso no login
            success_indicators = [
                "Dashboard",
                "dashboard",
                "Bem-vindo",
                "Welcome",
                "Menu",
                "Logout",
                "Sair"
            ]
            
            login_successful = False
            for indicator in success_indicators:
                try:
                    element = driver.find_element(By.XPATH, f"//*[contains(text(), '{indicator}')]")
                    print(f"✅ Indicador de sucesso encontrado: {indicator}")
                    login_successful = True
                    break
                except NoSuchElementException:
                    continue
            
            if login_successful:
                print("🎉 LOGIN REALIZADO COM SUCESSO!")
                driver.save_screenshot("login_success.png")
                return True
            else:
                print("❌ Login pode ter falhado - verificando erros...")
                
                # Procurar mensagens de erro
                error_selectors = [
                    ".error",
                    ".alert-danger",
                    ".text-red",
                    "[class*='error']",
                    "[class*='danger']"
                ]
                
                for selector in error_selectors:
                    try:
                        error_element = driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"❌ Erro encontrado: {error_element.text}")
                    except NoSuchElementException:
                        continue
                
                driver.save_screenshot("login_failed.png")
                print("📸 Screenshot de erro salvo como login_failed.png")
                return False
                
        except TimeoutException:
            print("⏰ Timeout - página não carregou completamente")
            driver.save_screenshot("timeout_debug.png")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False
        
    finally:
        if 'driver' in locals():
            driver.quit()
            print("🔚 Browser fechado")

def test_backend_connection():
    """Testar se o backend está respondendo"""
    import requests
    
    print("🔧 Testando conexão com backend...")
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend está respondendo")
            print(f"📊 Resposta: {response.json()}")
            return True
        else:
            print(f"❌ Backend retornou status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com backend: {e}")
        return False

def test_login_api():
    """Testar login via API"""
    import requests
    
    print("🔐 Testando login via API...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/api/v1/auth/login",
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Login via API bem-sucedido")
            token = response.json().get("access_token")
            print(f"🎫 Token recebido: {token[:20]}..." if token else "❌ Token não encontrado")
            return True
        else:
            print(f"❌ Login via API falhou: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro no login via API: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE COMPLETO DE LOGIN - FINAFLOW")
    print("=" * 50)
    
    # Testar backend primeiro
    backend_ok = test_backend_connection()
    
    # Testar login via API
    api_ok = test_login_api()
    
    # Testar frontend com Selenium
    frontend_ok = test_login()
    
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    print(f"🔧 Backend: {'✅ OK' if backend_ok else '❌ FALHOU'}")
    print(f"🔐 API Login: {'✅ OK' if api_ok else '❌ FALHOU'}")
    print(f"🌐 Frontend Login: {'✅ OK' if frontend_ok else '❌ FALHOU'}")
    
    if not frontend_ok:
        print("\n🔍 DEBUGGING:")
        print("1. Verifique se o frontend está rodando em http://localhost:3000")
        print("2. Verifique se o backend está rodando em http://127.0.0.1:8000")
        print("3. Verifique os screenshots gerados para debug")
        print("4. Verifique se as credenciais estão corretas")







