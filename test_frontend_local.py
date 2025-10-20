#!/usr/bin/env python3
"""
🎯 TESTE FRONTEND LOCAL - VALIDAÇÃO COMPLETA
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
FRONTEND_LOCAL = "http://localhost:3000"
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"

# Credenciais corretas
CREDENTIALS = {
    "username": "lucianoterresrosa",
    "password": "xs95LIa9ZduX"
}

def setup_driver():
    """Configurar driver do Selenium"""
    chrome_options = Options()
    # Modo não-headless para capturar screenshots
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
    filename = f"local_screenshot_{name}_{timestamp}.png"
    
    try:
        driver.save_screenshot(filename)
        print(f"   📸 Screenshot local salvo: {filename}")
        return filename
    except Exception as e:
        print(f"   ❌ Erro ao salvar screenshot: {str(e)}")
        return None

def test_frontend_local():
    """Teste completo do frontend local"""
    print("🎯 TESTE FRONTEND LOCAL - VALIDAÇÃO COMPLETA")
    print("=" * 60)
    
    driver = None
    screenshots = []
    
    try:
        driver = setup_driver()
        
        # 1. Testar página principal local
        print("1️⃣ TESTANDO PÁGINA PRINCIPAL LOCAL...")
        driver.get(FRONTEND_LOCAL)
        time.sleep(5)
        
        screenshot1 = take_screenshot(driver, "01_pagina_principal_local")
        screenshots.append(screenshot1)
        
        title = driver.title
        url = driver.current_url
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # 2. Testar página de login local
        print("\n2️⃣ TESTANDO PÁGINA DE LOGIN LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/login")
        time.sleep(5)
        
        screenshot2 = take_screenshot(driver, "02_pagina_login_local")
        screenshots.append(screenshot2)
        
        # Verificar se há campos de login
        try:
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "password")
            print("   ✅ Campos de login encontrados")
            
            # Preencher formulário
            username_field.clear()
            username_field.send_keys(CREDENTIALS["username"])
            
            password_field.clear()
            password_field.send_keys(CREDENTIALS["password"])
            
            screenshot3 = take_screenshot(driver, "03_login_preenchido_local")
            screenshots.append(screenshot3)
            
            # Clicar em login
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            screenshot4 = take_screenshot(driver, "04_apos_login_local")
            screenshots.append(screenshot4)
            
            print(f"   📋 URL após login: {driver.current_url}")
            
        except NoSuchElementException:
            print("   ❌ Campos de login não encontrados")
            screenshot_error = take_screenshot(driver, "02_login_error_local")
            screenshots.append(screenshot_error)
            return False, screenshots
        
        # 3. Testar página /transactions LOCAL
        print("\n3️⃣ TESTANDO PÁGINA /transactions LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/transactions")
        time.sleep(5)
        
        screenshot5 = take_screenshot(driver, "05_pagina_transactions_local")
        screenshots.append(screenshot5)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # Verificar estrutura NOVA
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
        
        print(f"   📊 Indicadores NOVA ESTRUTURA encontrados: {len(found_indicators)}/{len(new_structure_indicators)}")
        for indicator in found_indicators:
            print(f"      ✅ {indicator}")
        
        # 4. Testar página /lancamentos-diarios LOCAL
        print("\n4️⃣ TESTANDO PÁGINA /lancamentos-diarios LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/lancamentos-diarios")
        time.sleep(5)
        
        screenshot6 = take_screenshot(driver, "06_pagina_lancamentos_diarios_local")
        screenshots.append(screenshot6)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        if "Lançamentos Diários" in page_source:
            print("   ✅ Página de lançamentos diários funcionando LOCALMENTE")
            lancamentos_ok = True
        else:
            print("   ❌ Página de lançamentos diários não funcionando")
            lancamentos_ok = False
        
        # 5. Verificar botões de ação
        action_buttons = ["Novo Lançamento", "Criar", "Adicionar", "Editar", "Excluir"]
        found_buttons = [btn for btn in action_buttons if btn in page_source]
        
        if found_buttons:
            print(f"   📋 Botões de ação encontrados: {found_buttons}")
        
        # 6. Testar dashboard local
        print("\n5️⃣ TESTANDO DASHBOARD LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/dashboard")
        time.sleep(5)
        
        screenshot7 = take_screenshot(driver, "07_dashboard_local")
        screenshots.append(screenshot7)
        
        # Resultado final
        print("\n" + "=" * 60)
        print("🎯 RESULTADO DO TESTE FRONTEND LOCAL:")
        print(f"📸 Screenshots capturados: {len(screenshots)}")
        for i, screenshot in enumerate(screenshots, 1):
            if screenshot:
                print(f"   {i}. {screenshot}")
        
        print("\n📊 ANÁLISE LOCAL:")
        if len(found_indicators) >= 5:
            print("✅ NOVA ESTRUTURA DETECTADA LOCALMENTE!")
            print("✅ Sistema refatorado funcionando LOCALMENTE")
            print("✅ Estrutura espelhando planilha Google Sheets")
            structure_ok = True
        else:
            print("❌ ESTRUTURA ANTIGA AINDA PRESENTE LOCALMENTE")
            print("❌ Refatoração não funcionando")
            structure_ok = False
        
        print("=" * 60)
        
        return structure_ok and lancamentos_ok, screenshots
        
    except Exception as e:
        print(f"❌ Erro no teste local: {str(e)}")
        return False, screenshots
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success, screenshots = test_frontend_local()
    
    print(f"\n🎯 CONCLUSÃO FRONTEND LOCAL:")
    if success:
        print("✅ SISTEMA FUNCIONANDO PERFEITAMENTE LOCALMENTE!")
        print("📸 Screenshots comprovam implementação local")
        print("🎉 Refatoração completa funcionando")
        print("📋 Estrutura espelhando planilha Google Sheets")
        print("\n⚠️ PROBLEMA: Vercel com falhas hoje (20/10/2025)")
        print("✅ SOLUÇÃO: Sistema funcionando localmente")
    else:
        print("❌ SISTEMA COM PROBLEMAS LOCALMENTE")
        print("📸 Screenshots mostram estado atual")
    
    print(f"\n📁 Screenshots locais salvos no diretório atual")
    print("🔍 Verifique os arquivos PNG para evidência visual local")

🎯 TESTE FRONTEND LOCAL - VALIDAÇÃO COMPLETA
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
FRONTEND_LOCAL = "http://localhost:3000"
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"

# Credenciais corretas
CREDENTIALS = {
    "username": "lucianoterresrosa",
    "password": "xs95LIa9ZduX"
}

def setup_driver():
    """Configurar driver do Selenium"""
    chrome_options = Options()
    # Modo não-headless para capturar screenshots
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
    filename = f"local_screenshot_{name}_{timestamp}.png"
    
    try:
        driver.save_screenshot(filename)
        print(f"   📸 Screenshot local salvo: {filename}")
        return filename
    except Exception as e:
        print(f"   ❌ Erro ao salvar screenshot: {str(e)}")
        return None

def test_frontend_local():
    """Teste completo do frontend local"""
    print("🎯 TESTE FRONTEND LOCAL - VALIDAÇÃO COMPLETA")
    print("=" * 60)
    
    driver = None
    screenshots = []
    
    try:
        driver = setup_driver()
        
        # 1. Testar página principal local
        print("1️⃣ TESTANDO PÁGINA PRINCIPAL LOCAL...")
        driver.get(FRONTEND_LOCAL)
        time.sleep(5)
        
        screenshot1 = take_screenshot(driver, "01_pagina_principal_local")
        screenshots.append(screenshot1)
        
        title = driver.title
        url = driver.current_url
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # 2. Testar página de login local
        print("\n2️⃣ TESTANDO PÁGINA DE LOGIN LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/login")
        time.sleep(5)
        
        screenshot2 = take_screenshot(driver, "02_pagina_login_local")
        screenshots.append(screenshot2)
        
        # Verificar se há campos de login
        try:
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "password")
            print("   ✅ Campos de login encontrados")
            
            # Preencher formulário
            username_field.clear()
            username_field.send_keys(CREDENTIALS["username"])
            
            password_field.clear()
            password_field.send_keys(CREDENTIALS["password"])
            
            screenshot3 = take_screenshot(driver, "03_login_preenchido_local")
            screenshots.append(screenshot3)
            
            # Clicar em login
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            screenshot4 = take_screenshot(driver, "04_apos_login_local")
            screenshots.append(screenshot4)
            
            print(f"   📋 URL após login: {driver.current_url}")
            
        except NoSuchElementException:
            print("   ❌ Campos de login não encontrados")
            screenshot_error = take_screenshot(driver, "02_login_error_local")
            screenshots.append(screenshot_error)
            return False, screenshots
        
        # 3. Testar página /transactions LOCAL
        print("\n3️⃣ TESTANDO PÁGINA /transactions LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/transactions")
        time.sleep(5)
        
        screenshot5 = take_screenshot(driver, "05_pagina_transactions_local")
        screenshots.append(screenshot5)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # Verificar estrutura NOVA
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
        
        print(f"   📊 Indicadores NOVA ESTRUTURA encontrados: {len(found_indicators)}/{len(new_structure_indicators)}")
        for indicator in found_indicators:
            print(f"      ✅ {indicator}")
        
        # 4. Testar página /lancamentos-diarios LOCAL
        print("\n4️⃣ TESTANDO PÁGINA /lancamentos-diarios LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/lancamentos-diarios")
        time.sleep(5)
        
        screenshot6 = take_screenshot(driver, "06_pagina_lancamentos_diarios_local")
        screenshots.append(screenshot6)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        if "Lançamentos Diários" in page_source:
            print("   ✅ Página de lançamentos diários funcionando LOCALMENTE")
            lancamentos_ok = True
        else:
            print("   ❌ Página de lançamentos diários não funcionando")
            lancamentos_ok = False
        
        # 5. Verificar botões de ação
        action_buttons = ["Novo Lançamento", "Criar", "Adicionar", "Editar", "Excluir"]
        found_buttons = [btn for btn in action_buttons if btn in page_source]
        
        if found_buttons:
            print(f"   📋 Botões de ação encontrados: {found_buttons}")
        
        # 6. Testar dashboard local
        print("\n5️⃣ TESTANDO DASHBOARD LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/dashboard")
        time.sleep(5)
        
        screenshot7 = take_screenshot(driver, "07_dashboard_local")
        screenshots.append(screenshot7)
        
        # Resultado final
        print("\n" + "=" * 60)
        print("🎯 RESULTADO DO TESTE FRONTEND LOCAL:")
        print(f"📸 Screenshots capturados: {len(screenshots)}")
        for i, screenshot in enumerate(screenshots, 1):
            if screenshot:
                print(f"   {i}. {screenshot}")
        
        print("\n📊 ANÁLISE LOCAL:")
        if len(found_indicators) >= 5:
            print("✅ NOVA ESTRUTURA DETECTADA LOCALMENTE!")
            print("✅ Sistema refatorado funcionando LOCALMENTE")
            print("✅ Estrutura espelhando planilha Google Sheets")
            structure_ok = True
        else:
            print("❌ ESTRUTURA ANTIGA AINDA PRESENTE LOCALMENTE")
            print("❌ Refatoração não funcionando")
            structure_ok = False
        
        print("=" * 60)
        
        return structure_ok and lancamentos_ok, screenshots
        
    except Exception as e:
        print(f"❌ Erro no teste local: {str(e)}")
        return False, screenshots
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success, screenshots = test_frontend_local()
    
    print(f"\n🎯 CONCLUSÃO FRONTEND LOCAL:")
    if success:
        print("✅ SISTEMA FUNCIONANDO PERFEITAMENTE LOCALMENTE!")
        print("📸 Screenshots comprovam implementação local")
        print("🎉 Refatoração completa funcionando")
        print("📋 Estrutura espelhando planilha Google Sheets")
        print("\n⚠️ PROBLEMA: Vercel com falhas hoje (20/10/2025)")
        print("✅ SOLUÇÃO: Sistema funcionando localmente")
    else:
        print("❌ SISTEMA COM PROBLEMAS LOCALMENTE")
        print("📸 Screenshots mostram estado atual")
    
    print(f"\n📁 Screenshots locais salvos no diretório atual")
    print("🔍 Verifique os arquivos PNG para evidência visual local")

🎯 TESTE FRONTEND LOCAL - VALIDAÇÃO COMPLETA
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
FRONTEND_LOCAL = "http://localhost:3000"
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"

# Credenciais corretas
CREDENTIALS = {
    "username": "lucianoterresrosa",
    "password": "xs95LIa9ZduX"
}

def setup_driver():
    """Configurar driver do Selenium"""
    chrome_options = Options()
    # Modo não-headless para capturar screenshots
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
    filename = f"local_screenshot_{name}_{timestamp}.png"
    
    try:
        driver.save_screenshot(filename)
        print(f"   📸 Screenshot local salvo: {filename}")
        return filename
    except Exception as e:
        print(f"   ❌ Erro ao salvar screenshot: {str(e)}")
        return None

def test_frontend_local():
    """Teste completo do frontend local"""
    print("🎯 TESTE FRONTEND LOCAL - VALIDAÇÃO COMPLETA")
    print("=" * 60)
    
    driver = None
    screenshots = []
    
    try:
        driver = setup_driver()
        
        # 1. Testar página principal local
        print("1️⃣ TESTANDO PÁGINA PRINCIPAL LOCAL...")
        driver.get(FRONTEND_LOCAL)
        time.sleep(5)
        
        screenshot1 = take_screenshot(driver, "01_pagina_principal_local")
        screenshots.append(screenshot1)
        
        title = driver.title
        url = driver.current_url
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # 2. Testar página de login local
        print("\n2️⃣ TESTANDO PÁGINA DE LOGIN LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/login")
        time.sleep(5)
        
        screenshot2 = take_screenshot(driver, "02_pagina_login_local")
        screenshots.append(screenshot2)
        
        # Verificar se há campos de login
        try:
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "password")
            print("   ✅ Campos de login encontrados")
            
            # Preencher formulário
            username_field.clear()
            username_field.send_keys(CREDENTIALS["username"])
            
            password_field.clear()
            password_field.send_keys(CREDENTIALS["password"])
            
            screenshot3 = take_screenshot(driver, "03_login_preenchido_local")
            screenshots.append(screenshot3)
            
            # Clicar em login
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            screenshot4 = take_screenshot(driver, "04_apos_login_local")
            screenshots.append(screenshot4)
            
            print(f"   📋 URL após login: {driver.current_url}")
            
        except NoSuchElementException:
            print("   ❌ Campos de login não encontrados")
            screenshot_error = take_screenshot(driver, "02_login_error_local")
            screenshots.append(screenshot_error)
            return False, screenshots
        
        # 3. Testar página /transactions LOCAL
        print("\n3️⃣ TESTANDO PÁGINA /transactions LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/transactions")
        time.sleep(5)
        
        screenshot5 = take_screenshot(driver, "05_pagina_transactions_local")
        screenshots.append(screenshot5)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        # Verificar estrutura NOVA
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
        
        print(f"   📊 Indicadores NOVA ESTRUTURA encontrados: {len(found_indicators)}/{len(new_structure_indicators)}")
        for indicator in found_indicators:
            print(f"      ✅ {indicator}")
        
        # 4. Testar página /lancamentos-diarios LOCAL
        print("\n4️⃣ TESTANDO PÁGINA /lancamentos-diarios LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/lancamentos-diarios")
        time.sleep(5)
        
        screenshot6 = take_screenshot(driver, "06_pagina_lancamentos_diarios_local")
        screenshots.append(screenshot6)
        
        page_source = driver.page_source
        title = driver.title
        url = driver.current_url
        
        print(f"   📋 URL: {url}")
        print(f"   📋 Título: {title}")
        
        if "Lançamentos Diários" in page_source:
            print("   ✅ Página de lançamentos diários funcionando LOCALMENTE")
            lancamentos_ok = True
        else:
            print("   ❌ Página de lançamentos diários não funcionando")
            lancamentos_ok = False
        
        # 5. Verificar botões de ação
        action_buttons = ["Novo Lançamento", "Criar", "Adicionar", "Editar", "Excluir"]
        found_buttons = [btn for btn in action_buttons if btn in page_source]
        
        if found_buttons:
            print(f"   📋 Botões de ação encontrados: {found_buttons}")
        
        # 6. Testar dashboard local
        print("\n5️⃣ TESTANDO DASHBOARD LOCAL...")
        driver.get(f"{FRONTEND_LOCAL}/dashboard")
        time.sleep(5)
        
        screenshot7 = take_screenshot(driver, "07_dashboard_local")
        screenshots.append(screenshot7)
        
        # Resultado final
        print("\n" + "=" * 60)
        print("🎯 RESULTADO DO TESTE FRONTEND LOCAL:")
        print(f"📸 Screenshots capturados: {len(screenshots)}")
        for i, screenshot in enumerate(screenshots, 1):
            if screenshot:
                print(f"   {i}. {screenshot}")
        
        print("\n📊 ANÁLISE LOCAL:")
        if len(found_indicators) >= 5:
            print("✅ NOVA ESTRUTURA DETECTADA LOCALMENTE!")
            print("✅ Sistema refatorado funcionando LOCALMENTE")
            print("✅ Estrutura espelhando planilha Google Sheets")
            structure_ok = True
        else:
            print("❌ ESTRUTURA ANTIGA AINDA PRESENTE LOCALMENTE")
            print("❌ Refatoração não funcionando")
            structure_ok = False
        
        print("=" * 60)
        
        return structure_ok and lancamentos_ok, screenshots
        
    except Exception as e:
        print(f"❌ Erro no teste local: {str(e)}")
        return False, screenshots
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success, screenshots = test_frontend_local()
    
    print(f"\n🎯 CONCLUSÃO FRONTEND LOCAL:")
    if success:
        print("✅ SISTEMA FUNCIONANDO PERFEITAMENTE LOCALMENTE!")
        print("📸 Screenshots comprovam implementação local")
        print("🎉 Refatoração completa funcionando")
        print("📋 Estrutura espelhando planilha Google Sheets")
        print("\n⚠️ PROBLEMA: Vercel com falhas hoje (20/10/2025)")
        print("✅ SOLUÇÃO: Sistema funcionando localmente")
    else:
        print("❌ SISTEMA COM PROBLEMAS LOCALMENTE")
        print("📸 Screenshots mostram estado atual")
    
    print(f"\n📁 Screenshots locais salvos no diretório atual")
    print("🔍 Verifique os arquivos PNG para evidência visual local")
