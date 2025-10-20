#!/usr/bin/env python3
"""
🎯 TESTE VISUAL COM SCREENSHOTS - EVIDÊNCIA REAL
Sistema Lançamentos Diários - Espelhando Planilha Google Sheets
"""

import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Configurações
FRONTEND_URL = "https://finaflow.vercel.app"
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"

def setup_driver():
    """Configurar driver do Selenium com screenshots"""
    chrome_options = Options()
    # REMOVIDO --headless para capturar screenshots reais
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def take_screenshot(driver, name):
    """Capturar screenshot com timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{name}_{timestamp}.png"
    
    try:
        driver.save_screenshot(filename)
        print(f"   📸 Screenshot salvo: {filename}")
        return filename
    except Exception as e:
        print(f"   ❌ Erro ao salvar screenshot: {str(e)}")
        return None

def test_frontend_with_screenshots():
    """Teste visual completo com screenshots"""
    print("🎯 TESTE VISUAL COM SCREENSHOTS - EVIDÊNCIA REAL")
    print("=" * 60)
    
    driver = None
    screenshots = []
    
    try:
        driver = setup_driver()
        
        # 1. Testar página principal
        print("1️⃣ TESTANDO PÁGINA PRINCIPAL...")
        driver.get(FRONTEND_URL)
        time.sleep(5)
        
        screenshot1 = take_screenshot(driver, "01_pagina_principal")
        screenshots.append(screenshot1)
        
        title = driver.title
        url = driver.current_url
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # 2. Testar página de login
        print("\n2️⃣ TESTANDO PÁGINA DE LOGIN...")
        driver.get(f"{FRONTEND_URL}/login")
        time.sleep(5)
        
        screenshot2 = take_screenshot(driver, "02_pagina_login")
        screenshots.append(screenshot2)
        
        # Verificar se há campos de login
        try:
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "password")
            print("   ✅ Campos de login encontrados")
            
            # Preencher formulário com credenciais corretas
            username_field.clear()
            username_field.send_keys("lucianoterresrosa")
            
            password_field.clear()
            password_field.send_keys("xs95LIa9ZduX")
            
            screenshot3 = take_screenshot(driver, "03_login_preenchido")
            screenshots.append(screenshot3)
            
            # Clicar em login
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            screenshot4 = take_screenshot(driver, "04_apos_login")
            screenshots.append(screenshot4)
            
            print(f"   📋 URL após login: {driver.current_url}")
            
        except NoSuchElementException:
            print("   ❌ Campos de login não encontrados")
            screenshot_error = take_screenshot(driver, "02_login_error")
            screenshots.append(screenshot_error)
        
        # 3. Testar página /transactions
        print("\n3️⃣ TESTANDO PÁGINA /transactions...")
        driver.get(f"{FRONTEND_URL}/transactions")
        time.sleep(5)
        
        screenshot5 = take_screenshot(driver, "05_pagina_transactions")
        screenshots.append(screenshot5)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # Verificar estrutura
        structure_indicators = [
            "Lançamentos Financeiros",
            "Lançamentos Diários", 
            "Data Movimentação",
            "Valor",
            "Grupo",
            "Subgrupo",
            "Conta"
        ]
        
        found_indicators = []
        for indicator in structure_indicators:
            if indicator in page_source:
                found_indicators.append(indicator)
        
        print(f"   📊 Indicadores encontrados: {len(found_indicators)}/{len(structure_indicators)}")
        for indicator in found_indicators:
            print(f"      ✅ {indicator}")
        
        # 4. Testar página /lancamentos-diarios
        print("\n4️⃣ TESTANDO PÁGINA /lancamentos-diarios...")
        driver.get(f"{FRONTEND_URL}/lancamentos-diarios")
        time.sleep(5)
        
        screenshot6 = take_screenshot(driver, "06_pagina_lancamentos_diarios")
        screenshots.append(screenshot6)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        if "Lançamentos Diários" in page_source:
            print("   ✅ Página de lançamentos diários funcionando")
        else:
            print("   ❌ Página de lançamentos diários não funcionando")
        
        # 5. Testar dashboard
        print("\n5️⃣ TESTANDO DASHBOARD...")
        driver.get(f"{FRONTEND_URL}/dashboard")
        time.sleep(5)
        
        screenshot7 = take_screenshot(driver, "07_dashboard")
        screenshots.append(screenshot7)
        
        # 6. Verificar menu de navegação
        print("\n6️⃣ VERIFICANDO MENU DE NAVEGAÇÃO...")
        try:
            # Tentar encontrar menu
            menu_elements = driver.find_elements(By.TAG_NAME, "nav")
            if menu_elements:
                screenshot8 = take_screenshot(driver, "08_menu_navegacao")
                screenshots.append(screenshot8)
                print("   ✅ Menu de navegação encontrado")
            else:
                print("   ❌ Menu de navegação não encontrado")
        except:
            print("   ❌ Erro ao verificar menu")
        
        # Resultado final
        print("\n" + "=" * 60)
        print("🎯 RESULTADO DO TESTE COM SCREENSHOTS:")
        print(f"📸 Screenshots capturados: {len(screenshots)}")
        for i, screenshot in enumerate(screenshots, 1):
            if screenshot:
                print(f"   {i}. {screenshot}")
        
        print("\n📊 ANÁLISE:")
        if len(found_indicators) >= 3:
            print("✅ ESTRUTURA NOVA DETECTADA!")
            print("✅ Sistema refatorado funcionando")
        else:
            print("❌ ESTRUTURA ANTIGA AINDA PRESENTE")
            print("❌ Deploy do Vercel não processado")
        
        print("=" * 60)
        
        return len(found_indicators) >= 3, screenshots
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return False, screenshots
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success, screenshots = test_frontend_with_screenshots()
    
    print(f"\n🎯 CONCLUSÃO:")
    if success:
        print("✅ SISTEMA FUNCIONANDO COM EVIDÊNCIA VISUAL!")
        print("📸 Screenshots comprovam implementação")
    else:
        print("❌ SISTEMA AINDA COM PROBLEMAS")
        print("📸 Screenshots mostram estado atual")
    
    print(f"\n📁 Screenshots salvos no diretório atual")
    print("🔍 Verifique os arquivos PNG para evidência visual")
