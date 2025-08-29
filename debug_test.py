#!/usr/bin/env python3
"""
TESTE DE DEBUG - FinaFlow
Identificar problemas específicos na interface
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def debug_frontend():
    """Debug detalhado do frontend"""
    print("🔍 INICIANDO DEBUG DO FRONTEND")
    print("=" * 50)
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        # 1. Acessar página de login
        print("1️⃣ Acessando página de login...")
        driver.get("https://finaflow.vercel.app")
        
        # Aguardar carregamento
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Verificar título
        title = driver.title
        print(f"   📄 Título da página: '{title}'")
        
        # 2. Verificar elementos da página
        print("\n2️⃣ Verificando elementos da página...")
        
        # Procurar por diferentes tipos de campos
        selectors_to_try = [
            "input[name='username']",
            "input[name='email']", 
            "input[type='text']",
            "input[placeholder*='admin']",
            "input[placeholder*='email']",
            ".input",
            "input"
        ]
        
        for selector in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ Encontrado: {selector} - {len(elements)} elementos")
                    for i, elem in enumerate(elements[:3]):  # Mostrar apenas os 3 primeiros
                        placeholder = elem.get_attribute("placeholder") or "sem placeholder"
                        name = elem.get_attribute("name") or "sem name"
                        type_attr = elem.get_attribute("type") or "sem type"
                        print(f"      {i+1}. placeholder='{placeholder}', name='{name}', type='{type_attr}'")
                else:
                    print(f"   ❌ Não encontrado: {selector}")
            except Exception as e:
                print(f"   ⚠️ Erro ao procurar {selector}: {e}")
        
        # 3. Verificar estrutura HTML
        print("\n3️⃣ Verificando estrutura HTML...")
        
        # Procurar por formulários
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"   📝 Formulários encontrados: {len(forms)}")
        
        for i, form in enumerate(forms):
            print(f"   Formulário {i+1}:")
            inputs = form.find_elements(By.TAG_NAME, "input")
            print(f"     - Inputs: {len(inputs)}")
            for j, inp in enumerate(inputs):
                name = inp.get_attribute("name") or "sem name"
                type_attr = inp.get_attribute("type") or "sem type"
                placeholder = inp.get_attribute("placeholder") or "sem placeholder"
                print(f"       {j+1}. name='{name}', type='{type_attr}', placeholder='{placeholder}'")
        
        # 4. Verificar se há campos de login específicos
        print("\n4️⃣ Verificando campos de login...")
        
        # Procurar por campos que podem ser de login
        login_selectors = [
            "input[placeholder*='admin']",
            "input[placeholder*='email']", 
            "input[placeholder*='senha']",
            "input[placeholder*='password']",
            "input[type='password']"
        ]
        
        for selector in login_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"   ✅ Campo de login encontrado: {selector}")
                for elem in elements:
                    placeholder = elem.get_attribute("placeholder")
                    name = elem.get_attribute("name")
                    type_attr = elem.get_attribute("type")
                    print(f"     - placeholder='{placeholder}', name='{name}', type='{type_attr}'")
        
        # 5. Tentar fazer login
        print("\n5️⃣ Tentando fazer login...")
        
        # Procurar campo de email/username
        email_field = None
        for selector in ["input[placeholder*='admin']", "input[placeholder*='email']", "input[type='text']"]:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    email_field = elements[0]
                    print(f"   ✅ Campo de email encontrado: {selector}")
                    break
            except:
                continue
        
        if email_field:
            try:
                email_field.clear()
                email_field.send_keys("admin")
                print("   ✅ Email preenchido")
            except Exception as e:
                print(f"   ❌ Erro ao preencher email: {e}")
        
        # Procurar campo de senha
        password_field = None
        for selector in ["input[type='password']", "input[placeholder*='senha']"]:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    password_field = elements[0]
                    print(f"   ✅ Campo de senha encontrado: {selector}")
                    break
            except:
                continue
        
        if password_field:
            try:
                password_field.clear()
                password_field.send_keys("test")
                print("   ✅ Senha preenchida")
            except Exception as e:
                print(f"   ❌ Erro ao preencher senha: {e}")
        
        # Procurar botão de login
        login_button = None
        for selector in ["button[type='submit']", "button:contains('Entrar')", "button:contains('Login')"]:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    login_button = elements[0]
                    print(f"   ✅ Botão de login encontrado: {selector}")
                    break
            except:
                continue
        
        if login_button:
            try:
                button_text = login_button.text
                print(f"   📝 Texto do botão: '{button_text}'")
                login_button.click()
                print("   ✅ Botão clicado")
                
                # Aguardar redirecionamento
                time.sleep(3)
                current_url = driver.current_url
                print(f"   🔗 URL atual: {current_url}")
                
            except Exception as e:
                print(f"   ❌ Erro ao clicar no botão: {e}")
        
        # 6. Verificar se chegou no dashboard
        print("\n6️⃣ Verificando se chegou no dashboard...")
        
        if "dashboard" in driver.current_url:
            print("   ✅ Redirecionado para dashboard")
            
            # Procurar menu de navegação
            nav_selectors = [
                "nav",
                "[role='navigation']",
                ".sidebar",
                ".menu"
            ]
            
            for selector in nav_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ Navegação encontrada: {selector}")
                    break
            
            # Procurar link de usuários
            users_link_selectors = [
                "a[href*='users']",
                "a:contains('Usuários')",
                "a:contains('Users')"
            ]
            
            for selector in users_link_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ Link de usuários encontrado: {selector}")
                    break
        else:
            print("   ❌ Não foi redirecionado para dashboard")
        
    except Exception as e:
        print(f"❌ Erro durante debug: {e}")
    
    finally:
        driver.quit()
        print("\n" + "=" * 50)
        print("🏁 DEBUG CONCLUÍDO")

if __name__ == "__main__":
    debug_frontend()
