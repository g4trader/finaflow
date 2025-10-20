#!/usr/bin/env python3
"""
Teste detalhado do login para investigar problemas
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
USERNAME = "admin"
PASSWORD = "admin123"
TIMEOUT = 60  # Aumentar timeout

def test_login_detailed():
    """Teste detalhado do login"""
    print("🔍 TESTE DETALHADO DO LOGIN")
    print("="*50)
    
    # Configurar driver
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, TIMEOUT)
        
        print("✅ Driver configurado")
        
        # Navegar para login
        print(f"🌐 Navegando para: {FRONTEND_URL}/login")
        driver.get(f"{FRONTEND_URL}/login")
        
        # Aguardar página carregar
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)
        
        print("📄 Página carregada")
        driver.save_screenshot("login_page_detailed.png")
        
        # Verificar elementos
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar') or contains(text(), 'Login')]")
        
        print("✅ Elementos encontrados")
        
        # Preencher credenciais
        print(f"📝 Preenchendo: {USERNAME}")
        username_field.clear()
        username_field.send_keys(USERNAME)
        
        password_field.clear()
        password_field.send_keys(PASSWORD)
        
        time.sleep(2)
        driver.save_screenshot("login_filled_detailed.png")
        
        # Clicar no login
        print("🔑 Clicando em login...")
        login_button.click()
        
        # Aguardar resposta
        print("⏳ Aguardando resposta...")
        
        # Aguardar até 60 segundos por mudanças
        for i in range(60):
            current_url = driver.current_url
            print(f"   {i+1:2d}s - URL: {current_url}")
            
            # Verificar se mudou de página
            if current_url != f"{FRONTEND_URL}/login":
                print(f"✅ Redirecionamento detectado: {current_url}")
                driver.save_screenshot("login_success_detailed.png")
                break
            
            # Verificar se há mensagens de erro
            try:
                error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'erro') or contains(text(), 'error') or contains(text(), 'Erro') or contains(text(), 'Error')]")
                if error_elements:
                    print(f"⚠️ Possível erro detectado: {[el.text for el in error_elements]}")
                    driver.save_screenshot("login_error_detailed.png")
            except:
                pass
            
            time.sleep(1)
        
        # Verificar console do navegador
        print("\n🔍 Verificando console do navegador...")
        try:
            logs = driver.get_log('browser')
            for log in logs[-10:]:  # Últimos 10 logs
                if log['level'] in ['SEVERE', 'WARNING']:
                    print(f"   {log['level']}: {log['message']}")
        except:
            print("   Não foi possível acessar logs do console")
        
        # Verificar se há elementos de loading
        try:
            loading_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(text(), 'Carregando')]")
            if loading_elements:
                print(f"⏳ Elementos de loading encontrados: {len(loading_elements)}")
        except:
            pass
        
        # Aguardar mais um pouco e verificar novamente
        print("\n⏳ Aguardando mais 30 segundos...")
        time.sleep(30)
        
        final_url = driver.current_url
        print(f"📍 URL final: {final_url}")
        
        if final_url != f"{FRONTEND_URL}/login":
            print("✅ Login funcionou!")
            return True
        else:
            print("❌ Login não funcionou - ainda na página de login")
            
            # Verificar se há mensagens de erro na página
            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                if "erro" in page_text.lower() or "error" in page_text.lower():
                    print("⚠️ Possível erro na página:")
                    print(f"   {page_text[:500]}...")
            except:
                pass
            
            return False
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False
    
    finally:
        if 'driver' in locals():
            driver.quit()
            print("🔚 Driver fechado")

def main():
    """Função principal"""
    print("="*80)
    print("  🔍 TESTE DETALHADO DO LOGIN")
    print("="*80)
    print(f"🌐 URL: {FRONTEND_URL}")
    print(f"👤 Usuário: {USERNAME}")
    print(f"⏱️ Timeout: {TIMEOUT}s")
    print("="*80)
    
    result = test_login_detailed()
    
    print("\n" + "="*80)
    if result:
        print("🎉 LOGIN FUNCIONANDO!")
    else:
        print("❌ LOGIN COM PROBLEMAS")
    print("="*80)

if __name__ == "__main__":
    main()
