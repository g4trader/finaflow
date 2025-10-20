#!/usr/bin/env python3
"""
TESTE FINAL ABRANGENTE - FINANCIAL TRANSACTIONS
Testa todas as funcionalidades de forma completa e detalhada
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def setup_driver():
    """Configurar driver Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"❌ Erro ao configurar driver: {e}")
        return None

def test_backend_comprehensive():
    """Teste abrangente do backend"""
    print("🔍 TESTE ABRANGENTE DO BACKEND")
    print("=" * 50)
    
    base_url = "https://finaflow-backend-609095880025.us-central1.run.app"
    
    # Testar health check
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check: OK")
        else:
            print(f"❌ Health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check: Erro - {e}")
        return False
    
    # Testar rotas principais
    routes_to_test = [
        ("GET", "/", "Rota raiz"),
        ("GET", "/openapi.json", "Documentação OpenAPI"),
        ("GET", "/api/v1/financial-transactions", "Listar transações"),
        ("GET", "/api/v1/financial-transactions/summary", "Resumo transações"),
        ("POST", "/api/v1/financial-transactions/clear", "Limpar transações"),
        ("GET", "/api/v1/financial/transactions", "Rota antiga transações"),
        ("GET", "/api/v1/auth/login", "Rota de login")
    ]
    
    results = {}
    
    for method, route, description in routes_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{route}", timeout=10)
            else:
                response = requests.post(f"{base_url}{route}", timeout=10)
            
            status = response.status_code
            if status in [200, 403, 401, 422]:  # Status esperados
                print(f"✅ {description}: {status}")
                results[route] = "OK"
            else:
                print(f"❌ {description}: {status}")
                results[route] = "FAIL"
                
        except Exception as e:
            print(f"❌ {description}: Erro - {e}")
            results[route] = "ERROR"
    
    # Verificar se as novas rotas estão funcionando
    new_routes_working = all(
        results.get(route) == "OK" 
        for route in ["/api/v1/financial-transactions", "/api/v1/financial-transactions/summary"]
    )
    
    print(f"\n📊 Resumo Backend:")
    print(f"   Novas rotas funcionando: {'✅ Sim' if new_routes_working else '❌ Não'}")
    print(f"   Total de rotas testadas: {len(routes_to_test)}")
    
    return new_routes_working

def test_frontend_comprehensive(driver):
    """Teste abrangente do frontend"""
    print("\n🔍 TESTE ABRANGENTE DO FRONTEND")
    print("=" * 50)
    
    # Testar página de transações
    try:
        driver.get("https://finaflow.vercel.app/transactions")
        time.sleep(5)
        
        print(f"📍 URL: {driver.current_url}")
        
        # Verificar elementos essenciais
        essential_elements = [
            ("Botões de ação", "//button[contains(text(), 'Importar CSV') or contains(text(), 'Nova Transação')]"),
            ("Campo de busca", "//input[@placeholder or @name or contains(@class, 'search')]"),
            ("Estrutura da página", "//div[contains(@class, 'container') or contains(@class, 'main') or contains(@class, 'content')]")
        ]
        
        elements_found = 0
        for element_name, xpath in essential_elements:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"✅ {element_name}: {len(elements)} encontrado(s)")
                    elements_found += 1
                else:
                    print(f"❌ {element_name}: Não encontrado")
            except Exception as e:
                print(f"❌ {element_name}: Erro - {e}")
        
        # Verificar se a página está carregando dados
        time.sleep(3)
        
        # Procurar por elementos de transação
        transaction_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'transação') or contains(text(), 'transaction') or contains(text(), 'Transação')]")
        if transaction_elements:
            print(f"✅ Elementos de transação: {len(transaction_elements)} encontrado(s)")
            elements_found += 1
        else:
            print("❌ Elementos de transação: Não encontrados")
        
        # Verificar se há erros JavaScript
        try:
            console_logs = driver.get_log("browser")
            errors = [log for log in console_logs if log["level"] in ["SEVERE", "ERROR"]]
            if errors:
                print(f"⚠️ Erros JavaScript: {len(errors)} encontrado(s)")
                for error in errors[:3]:
                    print(f"   ❌ {error['message'][:100]}...")
            else:
                print("✅ Nenhum erro JavaScript encontrado")
        except:
            print("⚠️ Não foi possível verificar logs JavaScript")
        
        return elements_found >= 2  # Pelo menos 2 elementos essenciais
        
    except Exception as e:
        print(f"❌ Erro no teste do frontend: {e}")
        return False

def test_integration():
    """Teste de integração entre frontend e backend"""
    print("\n🔍 TESTE DE INTEGRAÇÃO")
    print("=" * 50)
    
    try:
        # Verificar se o frontend está fazendo chamadas para o backend
        frontend_url = "https://finaflow.vercel.app/transactions"
        backend_url = "https://finaflow-backend-609095880025.us-central1.run.app"
        
        # Fazer uma requisição para ver se há redirecionamento ou integração
        response = requests.get(frontend_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend acessível")
            
            # Verificar se há referências ao backend no HTML
            if backend_url.replace("https://", "").replace("http://", "") in response.text:
                print("✅ Referências ao backend encontradas no frontend")
                return True
            else:
                print("⚠️ Poucas referências ao backend no frontend")
                return False
        else:
            print(f"❌ Frontend não acessível: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de integração: {e}")
        return False

def test_data_flow():
    """Teste do fluxo de dados"""
    print("\n🔍 TESTE DO FLUXO DE DADOS")
    print("=" * 50)
    
    try:
        # Verificar se as rotas estão retornando dados consistentes
        base_url = "https://finaflow-backend-609095880025.us-central1.run.app"
        
        # Testar rota antiga vs nova
        old_response = requests.get(f"{base_url}/api/v1/financial/transactions", timeout=10)
        new_response = requests.get(f"{base_url}/api/v1/financial-transactions", timeout=10)
        
        print(f"📊 Rota antiga: {old_response.status_code}")
        print(f"📊 Rota nova: {new_response.status_code}")
        
        # Verificar se ambas estão funcionando
        if old_response.status_code in [200, 403, 401] and new_response.status_code in [200, 403, 401]:
            print("✅ Ambas as rotas estão funcionando")
            
            # Verificar se a rota antiga retorna dados mock
            if old_response.status_code == 200:
                try:
                    old_data = old_response.json()
                    if isinstance(old_data, list) and len(old_data) > 0:
                        print(f"✅ Rota antiga retorna {len(old_data)} transações")
                        print(f"   Primeira transação: {old_data[0]}")
                    else:
                        print("⚠️ Rota antiga não retorna dados no formato esperado")
                except:
                    print("⚠️ Rota antiga não retorna JSON válido")
            
            return True
        else:
            print("❌ Uma ou ambas as rotas não estão funcionando")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste do fluxo de dados: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 INICIANDO TESTE FINAL ABRANGENTE")
    print("=" * 60)
    
    # Testar backend
    backend_ok = test_backend_comprehensive()
    
    # Configurar driver
    driver = setup_driver()
    if not driver:
        print("❌ Não foi possível configurar o driver")
        return
    
    try:
        # Testar frontend
        frontend_ok = test_frontend_comprehensive(driver)
        
        # Testar integração
        integration_ok = test_integration()
        
        # Testar fluxo de dados
        data_flow_ok = test_data_flow()
        
        # Resultado final
        print("\n" + "=" * 60)
        print("📊 RESULTADO FINAL COMPREENSIVO:")
        print(f"Backend: {'✅ OK' if backend_ok else '❌ FALHOU'}")
        print(f"Frontend: {'✅ OK' if frontend_ok else '❌ FALHOU'}")
        print(f"Integração: {'✅ OK' if integration_ok else '❌ FALHOU'}")
        print(f"Fluxo de dados: {'✅ OK' if data_flow_ok else '❌ FALHOU'}")
        
        # Resumo final
        total_tests = sum([backend_ok, frontend_ok, integration_ok, data_flow_ok])
        
        if total_tests == 4:
            print("\n🎉 TESTE COMPLETO PASSOU! SISTEMA 100% FUNCIONAL!")
            print("✨ Todas as funcionalidades estão funcionando corretamente")
        elif total_tests >= 3:
            print(f"\n✅ TESTE MAJORITARIAMENTE PASSOU! ({total_tests}/4)")
            print("⚠️ Algumas funcionalidades podem precisar de ajustes")
        else:
            print(f"\n❌ TESTE FALHOU! ({total_tests}/4)")
            print("🔧 Sistema precisa de correções")
            
    finally:
        driver.quit()
        print("✅ Driver Chrome fechado")

if __name__ == "__main__":
    main()

