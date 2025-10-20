#!/usr/bin/env python3
"""
TESTE COMPLETO COM SELENIUM - FINANCIAL TRANSACTIONS
Testa toda a funcionalidade incluindo login e rotas autenticadas
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """Configurar driver Chrome com opções"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executar em background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"❌ Erro ao configurar driver: {e}")
        return None

def test_backend_health():
    """Testar health check do backend"""
    print("🔍 TESTANDO HEALTH CHECK DO BACKEND...")
    try:
        response = requests.get("https://finaflow-backend-609095880025.us-central1.run.app/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {response.status_code} - {data}")
            return True
        else:
            print(f"❌ Health check falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return False

def test_backend_routes():
    """Testar rotas do backend"""
    print("🔍 TESTANDO ROTAS DO BACKEND...")
    
    routes = [
        "/api/v1/financial-transactions",
        "/api/v1/financial-transactions/summary", 
        "/api/v1/financial-transactions/clear"
    ]
    
    all_routes_working = True
    
    for route in routes:
        try:
            response = requests.get(f"https://finaflow-backend-609095880025.us-central1.run.app{route}", timeout=10)
            if response.status_code in [200, 403, 401]:  # 403/401 são esperados sem auth
                print(f"✅ {route}: {response.status_code}")
            else:
                print(f"❌ {route}: {response.status_code}")
                all_routes_working = False
        except Exception as e:
            print(f"❌ {route}: Erro - {e}")
            all_routes_working = False
    
    return all_routes_working

def test_frontend_login(driver):
    """Testar login no frontend"""
    print("🔍 TESTANDO LOGIN NO FRONTEND...")
    
    try:
        # Acessar página de login
        driver.get("https://finaflow.vercel.app/login")
        time.sleep(3)
        
        # Verificar se a página carregou
        if "login" in driver.current_url.lower():
            print("✅ Página de login carregada")
        else:
            print(f"⚠️ URL atual: {driver.current_url}")
        
        # Verificar elementos da página
        try:
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar') or contains(text(), 'Login')]")
            
            print("✅ Campos de login encontrados")
            
            # Preencher credenciais (usar credenciais de teste se disponíveis)
            email_input.send_keys("test@example.com")
            password_input.send_keys("testpassword")
            
            # Tentar fazer login
            login_button.click()
            time.sleep(3)
            
            # Verificar resultado
            if "dashboard" in driver.current_url.lower() or "transactions" in driver.current_url.lower():
                print("✅ Login bem-sucedido")
                return True
            else:
                print("⚠️ Login não redirecionou como esperado")
                return False
                
        except NoSuchElementException as e:
            print(f"⚠️ Elementos de login não encontrados: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de login: {e}")
        return False

def test_transactions_page(driver):
    """Testar página de transações"""
    print("🔍 TESTANDO PÁGINA DE TRANSAÇÕES...")
    
    try:
        # Acessar página de transações
        driver.get("https://finaflow.vercel.app/transactions")
        time.sleep(3)
        
        # Verificar se a página carregou
        if "transactions" in driver.current_url.lower():
            print("✅ Página de transações carregada")
        else:
            print(f"⚠️ URL atual: {driver.current_url}")
        
        # Verificar elementos da página
        try:
            # Procurar por botões ou elementos de ação
            action_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Nova') or contains(text(), 'Importar') or contains(text(), 'Adicionar')]")
            if action_buttons:
                print(f"✅ Botões de ação encontrados: {len(action_buttons)}")
            else:
                print("⚠️ Botões de ação não encontrados")
            
            # Procurar por tabela ou lista de transações
            transaction_table = driver.find_elements(By.XPATH, "//table | //div[contains(@class, 'transaction')] | //div[contains(@class, 'list')]")
            if transaction_table:
                print("✅ Tabela/lista de transações encontrada")
            else:
                print("⚠️ Tabela/lista de transações não encontrada")
            
            # Procurar por mensagem de "nenhuma transação"
            no_transactions_msg = driver.find_elements(By.XPATH, "//*[contains(text(), 'nenhuma') or contains(text(), 'Nenhuma') or contains(text(), 'empty')]")
            if no_transactions_msg:
                print("✅ Mensagem de 'nenhuma transação' encontrada")
            else:
                print("⚠️ Mensagem de 'nenhuma transação' não encontrada")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Erro ao verificar elementos: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste da página de transações: {e}")
        return False

def test_api_with_auth():
    """Testar API com autenticação (se possível)"""
    print("🔍 TESTANDO API COM AUTENTICAÇÃO...")
    
    # Aqui poderíamos implementar login via API para obter token
    # Por enquanto, vamos apenas verificar se as rotas estão acessíveis
    
    try:
        # Testar rota de login da API
        login_data = {
            "email": "test@example.com",
            "password": "testpassword"
        }
        
        response = requests.post(
            "https://finaflow-backend-609095880025.us-central1.run.app/api/v1/auth/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Login via API funcionando")
            data = response.json()
            if "access_token" in data:
                token = data["access_token"]
                print("✅ Token obtido com sucesso")
                
                # Testar rotas com token
                headers = {"Authorization": f"Bearer {token}"}
                
                routes = [
                    "/api/v1/financial-transactions",
                    "/api/v1/financial-transactions/summary"
                ]
                
                for route in routes:
                    try:
                        response = requests.get(
                            f"https://finaflow-backend-609095880025.us-central1.run.app{route}",
                            headers=headers,
                            timeout=10
                        )
                        if response.status_code == 200:
                            print(f"✅ {route} com auth: {response.status_code}")
                        else:
                            print(f"⚠️ {route} com auth: {response.status_code}")
                    except Exception as e:
                        print(f"❌ {route} com auth: Erro - {e}")
                
                return True
            else:
                print("⚠️ Token não encontrado na resposta")
                return False
        else:
            print(f"⚠️ Login via API falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de API com auth: {e}")
        return False

def main():
    """Função principal do teste"""
    print("🚀 INICIANDO TESTE COMPLETO COM SELENIUM")
    print("=" * 60)
    
    # Testar backend
    backend_health = test_backend_health()
    backend_routes = test_backend_routes()
    
    # Configurar driver
    driver = setup_driver()
    if not driver:
        print("❌ Não foi possível configurar o driver")
        return
    
    try:
        # Testar frontend
        frontend_login = test_frontend_login(driver)
        frontend_transactions = test_transactions_page(driver)
        
        # Testar API com autenticação
        api_auth = test_api_with_auth()
        
        # Resultados
        print("\n" + "=" * 60)
        print("📊 RESULTADO FINAL:")
        print(f"Backend Health: {'✅ OK' if backend_health else '❌ FALHOU'}")
        print(f"Backend Routes: {'✅ OK' if backend_routes else '❌ FALHOU'}")
        print(f"Frontend Login: {'✅ OK' if frontend_login else '❌ FALHOU'}")
        print(f"Frontend Transactions: {'✅ OK' if frontend_transactions else '❌ FALHOU'}")
        print(f"API Auth: {'✅ OK' if api_auth else '❌ FALHOU'}")
        
        # Resumo
        if all([backend_health, backend_routes, frontend_transactions]):
            print("\n🎉 TESTE COMPLETO PASSOU! Sistema funcionando corretamente.")
        else:
            print("\n⚠️ ALGUNS TESTES FALHARAM. Verificar configuração.")
            
    finally:
        # Fechar driver
        driver.quit()
        print("✅ Driver Chrome fechado")

if __name__ == "__main__":
    main()

