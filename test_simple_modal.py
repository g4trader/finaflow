#!/usr/bin/env python3
"""
Teste simples para verificar se o botão Novo Usuário está funcionando
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_simple_modal():
    """Teste simples para verificar o botão Novo Usuário"""
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🧪 Teste simples da modal...")
        
        # 1. Login
        print("1. Fazendo login...")
        driver.get("https://finaflow.vercel.app/login")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin@finaflow.com")
        password_field.send_keys("admin123")
        
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
        login_button.click()
        
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        print("✅ Login realizado")
        
        # 2. Navegar para usuários
        print("2. Navegando para página de usuários...")
        driver.get("https://finaflow.vercel.app/users")
        
        # Aguardar carregamento da página
        time.sleep(3)
        
        # Verificar se a página carregou
        print(f"   URL atual: {driver.current_url}")
        
        # Procurar pelo botão Novo Usuário
        try:
            novo_usuario_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Novo Usuário')]")
            print("✅ Botão 'Novo Usuário' encontrado")
            
            # Verificar se o botão está visível e clicável
            if novo_usuario_btn.is_displayed():
                print("✅ Botão está visível")
            else:
                print("❌ Botão não está visível")
                
            if novo_usuario_btn.is_enabled():
                print("✅ Botão está habilitado")
            else:
                print("❌ Botão não está habilitado")
            
            # Tentar clicar no botão
            print("3. Clicando no botão Novo Usuário...")
            novo_usuario_btn.click()
            
            # Aguardar um pouco
            time.sleep(2)
            
            # Verificar se algo mudou na página
            print(f"   URL após clique: {driver.current_url}")
            
            # Procurar por elementos da modal
            try:
                modal_title = driver.find_element(By.XPATH, "//h3[contains(text(), 'Novo Usuário')]")
                print("✅ Modal aberta com sucesso!")
                
                # Verificar se há campos na modal
                try:
                    nome_field = driver.find_element(By.XPATH, "//input[@placeholder='Digite o nome']")
                    print("✅ Campo nome encontrado na modal")
                except:
                    print("❌ Campo nome não encontrado na modal")
                    
            except:
                print("❌ Modal não foi aberta")
                
                # Verificar se há algum erro na página
                page_source = driver.page_source
                if "error" in page_source.lower():
                    print("   ⚠️ Página contém texto de erro")
                
                # Listar todos os botões na página
                buttons = driver.find_elements(By.TAG_NAME, "button")
                print(f"   Botões encontrados na página: {len(buttons)}")
                for i, btn in enumerate(buttons[:5]):  # Mostrar apenas os primeiros 5
                    try:
                        text = btn.text
                        print(f"   Botão {i+1}: '{text}'")
                    except:
                        print(f"   Botão {i+1}: [sem texto]")
                
        except Exception as e:
            print(f"❌ Erro ao encontrar botão 'Novo Usuário': {e}")
            
            # Listar todos os elementos que contêm "Novo" ou "Usuário"
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Novo') or contains(text(), 'Usuário')]")
            print(f"   Elementos com 'Novo' ou 'Usuário': {len(elements)}")
            for elem in elements[:3]:
                try:
                    print(f"   - {elem.text}")
                except:
                    pass
        
        print("\n🎉 Teste simples concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_simple_modal()
