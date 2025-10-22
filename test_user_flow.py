#!/usr/bin/env python3
"""
Teste automatizado do fluxo do usuário no FinaFlow
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import sys

# Configurações
FRONTEND_URL = "https://finaflow.vercel.app"
USERNAME = "admin"
PASSWORD = "admin123"

def setup_driver():
    """Configura o Chrome driver"""
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Comentado para ver o navegador
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def print_step(step_number, description):
    """Imprime passo do teste"""
    print(f"\n{'='*80}")
    print(f"  PASSO {step_number}: {description}")
    print(f"{'='*80}")

def test_user_flow():
    """Testa o fluxo completo do usuário"""
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)
    
    try:
        # PASSO 1: Acessar página de login
        print_step(1, "Acessando página de login")
        driver.get(f"{FRONTEND_URL}/login")
        time.sleep(2)
        
        print(f"   URL atual: {driver.current_url}")
        print(f"   Título: {driver.title}")
        
        # PASSO 2: Preencher credenciais
        print_step(2, "Preenchendo credenciais")
        
        # Localizar campos
        username_field = wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")
        
        print(f"   ✅ Campos de login encontrados")
        
        # Preencher
        username_field.clear()
        username_field.send_keys(USERNAME)
        print(f"   ✅ Username preenchido: {USERNAME}")
        
        password_field.clear()
        password_field.send_keys(PASSWORD)
        print(f"   ✅ Password preenchido: {'*' * len(PASSWORD)}")
        
        # Screenshot antes do login
        driver.save_screenshot('/tmp/1_before_login.png')
        print(f"   📸 Screenshot salvo: /tmp/1_before_login.png")
        
        # PASSO 3: Submeter formulário
        print_step(3, "Clicando em Login")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        print(f"   ✅ Botão de login clicado")
        print(f"   ⏳ Aguardando resposta...")
        
        time.sleep(3)
        
        # PASSO 4: Verificar redirecionamento
        print_step(4, "Verificando redirecionamento")
        
        current_url = driver.current_url
        print(f"   URL atual: {current_url}")
        
        driver.save_screenshot('/tmp/2_after_login.png')
        print(f"   📸 Screenshot salvo: /tmp/2_after_login.png")
        
        # Verificar console logs (erros JavaScript)
        logs = driver.get_log('browser')
        if logs:
            print(f"\n   📋 Console Logs:")
            for log in logs[-5:]:  # Últimos 5 logs
                level = log['level']
                message = log['message']
                emoji = "❌" if level == "SEVERE" else "⚠️" if level == "WARNING" else "ℹ️"
                print(f"      {emoji} [{level}] {message}")
        
        # PASSO 5: Verificar página atual
        print_step(5, "Analisando página atual")
        
        if "select-business-unit" in current_url:
            print(f"   ✅ Redirecionado para seleção de empresa")
            
            # Aguardar carregamento
            time.sleep(2)
            
            # Tentar encontrar empresas disponíveis
            try:
                companies = driver.find_elements(By.CSS_SELECTOR, "[data-testid='company-option'], .company-card, button")
                print(f"   📊 Elementos encontrados: {len(companies)}")
                
                # Verificar texto na página
                page_text = driver.find_element(By.TAG_NAME, "body").text
                print(f"\n   📄 Conteúdo da página:")
                print(f"   {'-'*76}")
                for line in page_text.split('\n')[:15]:  # Primeiras 15 linhas
                    print(f"   {line}")
                print(f"   {'-'*76}")
                
                # Screenshot
                driver.save_screenshot('/tmp/3_select_company.png')
                print(f"\n   📸 Screenshot salvo: /tmp/3_select_company.png")
                
                # Tentar selecionar primeira empresa
                if companies:
                    print(f"\n   🎯 Tentando selecionar primeira empresa...")
                    companies[0].click()
                    time.sleep(3)
                    
                    final_url = driver.current_url
                    print(f"   URL final: {final_url}")
                    
                    driver.save_screenshot('/tmp/4_after_select.png')
                    print(f"   📸 Screenshot salvo: /tmp/4_after_select.png")
                    
                    if "dashboard" in final_url or final_url == f"{FRONTEND_URL}/":
                        print(f"\n   🎉 SUCESSO! Redirecionado para o dashboard!")
                    else:
                        print(f"\n   ⚠️ Redirecionado para: {final_url}")
                else:
                    print(f"   ⚠️ Nenhuma empresa encontrada para selecionar")
                    
            except Exception as e:
                print(f"   ❌ Erro ao procurar empresas: {e}")
                
        elif "dashboard" in current_url or current_url == f"{FRONTEND_URL}/":
            print(f"   ✅ Redirecionado direto para o dashboard!")
            driver.save_screenshot('/tmp/3_dashboard.png')
            print(f"   📸 Screenshot salvo: /tmp/3_dashboard.png")
            
        elif "login" in current_url:
            print(f"   ❌ Ainda na página de login - Login pode ter falhado")
            
            # Verificar mensagens de erro
            try:
                error_msg = driver.find_element(By.CSS_SELECTOR, ".error, .alert, [role='alert']")
                print(f"   ❌ Erro: {error_msg.text}")
            except:
                print(f"   ℹ️ Nenhuma mensagem de erro visível")
        else:
            print(f"   ⚠️ Página inesperada: {current_url}")
        
        # PASSO 6: Resumo final
        print_step(6, "RESUMO DO TESTE")
        
        print(f"\n   📊 Estatísticas:")
        print(f"      - URL inicial: {FRONTEND_URL}/login")
        print(f"      - URL final: {driver.current_url}")
        print(f"      - Screenshots salvos em: /tmp/")
        
        # Manter navegador aberto por 10 segundos
        print(f"\n   ⏱️ Mantendo navegador aberto por 10 segundos...")
        print(f"   (Você pode inspecionar manualmente)")
        time.sleep(10)
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot('/tmp/error.png')
        print(f"   📸 Screenshot do erro salvo: /tmp/error.png")
        
    finally:
        print(f"\n{'='*80}")
        print(f"  🏁 TESTE FINALIZADO")
        print(f"{'='*80}")
        driver.quit()

if __name__ == "__main__":
    test_user_flow()


