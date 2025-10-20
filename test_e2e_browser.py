#!/usr/bin/env python3
"""
Teste End-to-End completo no navegador usando Selenium
Testa todo o fluxo: login → seleção de business unit → dashboard
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
TIMEOUT = 30
SCREENSHOTS_DIR = "e2e_screenshots"

class E2ETester:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.results = {
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "screenshots": [],
            "errors": []
        }
        
    def setup_driver(self):
        """Configura o driver do Selenium"""
        print("🔧 Configurando driver do Chrome...")
        
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        # Desabilitar logs desnecessários
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, TIMEOUT)
            print("✅ Driver configurado com sucesso")
            return True
        except Exception as e:
            print(f"❌ Erro ao configurar driver: {e}")
            return False
    
    def take_screenshot(self, name):
        """Tira screenshot da página atual"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{SCREENSHOTS_DIR}/{name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            self.results["screenshots"].append(filename)
            print(f"📸 Screenshot: {filename}")
            return filename
        except Exception as e:
            print(f"⚠️ Erro ao tirar screenshot: {e}")
            return None
    
    def test_login_page(self):
        """Testa a página de login"""
        print("\n🔐 TESTE 1: Página de Login")
        print("="*50)
        
        try:
            # Navegar para a página de login
            print("🌐 Navegando para a página de login...")
            self.driver.get(f"{FRONTEND_URL}/login")
            
            # Aguardar página carregar
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            # Screenshot da página de login
            self.take_screenshot("01_login_page")
            
            # Verificar elementos da página de login
            username_field = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_field = self.driver.find_element(By.NAME, "password")
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar') or contains(text(), 'Login')]")
            
            print("✅ Elementos da página de login encontrados")
            print(f"   - Campo username: {username_field.is_displayed()}")
            print(f"   - Campo password: {password_field.is_displayed()}")
            print(f"   - Botão login: {login_button.is_displayed()}")
            
            # Preencher credenciais
            print(f"📝 Preenchendo credenciais: {USERNAME}")
            username_field.clear()
            username_field.send_keys(USERNAME)
            
            password_field.clear()
            password_field.send_keys(PASSWORD)
            
            time.sleep(1)
            self.take_screenshot("02_login_filled")
            
            # Clicar no botão de login
            print("🔑 Clicando no botão de login...")
            login_button.click()
            
            # Aguardar redirecionamento
            time.sleep(5)
            
            # Verificar se foi redirecionado
            current_url = self.driver.current_url
            print(f"📍 URL atual: {current_url}")
            
            if "select-business-unit" in current_url:
                print("✅ Redirecionamento para seleção de business unit - SUCESSO")
                self.take_screenshot("03_redirected_to_business_unit")
                return True
            else:
                print("⚠️ Não foi redirecionado para a página esperada")
                self.take_screenshot("03_login_result")
                return False
                
        except TimeoutException:
            print("❌ Timeout ao carregar página de login")
            self.take_screenshot("error_login_timeout")
            return False
        except Exception as e:
            print(f"❌ Erro no teste de login: {e}")
            self.take_screenshot("error_login")
            return False
    
    def test_business_unit_selection(self):
        """Testa a seleção de business unit"""
        print("\n🏢 TESTE 2: Seleção de Business Unit")
        print("="*50)
        
        try:
            # Aguardar página carregar
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            self.take_screenshot("04_business_unit_page")
            
            # Verificar se há business units disponíveis
            try:
                business_units = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='business-unit-item'], .business-unit-item, .card")
                print(f"📊 Business units encontrados: {len(business_units)}")
                
                if len(business_units) > 0:
                    # Selecionar a primeira business unit
                    first_bu = business_units[0]
                    print("🎯 Selecionando primeira business unit...")
                    
                    # Procurar botão de seleção ou link
                    try:
                        select_button = first_bu.find_element(By.XPATH, ".//button[contains(text(), 'Selecionar') or contains(text(), 'Select')]")
                        select_button.click()
                    except NoSuchElementException:
                        # Se não encontrar botão, tentar clicar na própria div
                        first_bu.click()
                    
                    time.sleep(3)
                    self.take_screenshot("05_business_unit_selected")
                    
                    # Verificar redirecionamento
                    current_url = self.driver.current_url
                    print(f"📍 URL após seleção: {current_url}")
                    
                    if "dashboard" in current_url or current_url == FRONTEND_URL + "/" or "home" in current_url:
                        print("✅ Redirecionamento para dashboard - SUCESSO")
                        return True
                    else:
                        print("⚠️ Redirecionamento não detectado")
                        return False
                else:
                    print("⚠️ Nenhuma business unit encontrada")
                    return False
                    
            except Exception as e:
                print(f"❌ Erro ao selecionar business unit: {e}")
                self.take_screenshot("error_business_unit")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste de business unit: {e}")
            return False
    
    def test_dashboard(self):
        """Testa o dashboard principal"""
        print("\n📊 TESTE 3: Dashboard Principal")
        print("="*50)
        
        try:
            # Aguardar página carregar
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            self.take_screenshot("06_dashboard_loaded")
            
            # Verificar elementos do dashboard
            try:
                # Procurar por elementos típicos de dashboard
                dashboard_elements = [
                    "//h1[contains(text(), 'Dashboard')]",
                    "//h2[contains(text(), 'Dashboard')]",
                    "//div[contains(@class, 'dashboard')]",
                    "//nav",
                    "//header"
                ]
                
                found_elements = []
                for xpath in dashboard_elements:
                    try:
                        element = self.driver.find_element(By.XPATH, xpath)
                        if element.is_displayed():
                            found_elements.append(xpath)
                    except NoSuchElementException:
                        pass
                
                print(f"✅ Elementos do dashboard encontrados: {len(found_elements)}")
                
                # Verificar se há dados de transações
                try:
                    transaction_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'R$') or contains(text(), 'receita') or contains(text(), 'despesa')]")
                    print(f"💰 Elementos de transação encontrados: {len(transaction_elements)}")
                    
                    if len(transaction_elements) > 0:
                        print("✅ Dados de transações visíveis no dashboard")
                    else:
                        print("⚠️ Nenhum dado de transação visível")
                        
                except Exception as e:
                    print(f"⚠️ Erro ao verificar transações: {e}")
                
                # Verificar navegação
                try:
                    nav_links = self.driver.find_elements(By.XPATH, "//nav//a | //header//a")
                    print(f"🧭 Links de navegação encontrados: {len(nav_links)}")
                    
                    for i, link in enumerate(nav_links[:5]):  # Mostrar apenas os primeiros 5
                        try:
                            text = link.text.strip()
                            href = link.get_attribute("href")
                            if text and href:
                                print(f"   {i+1}. {text} -> {href}")
                        except:
                            pass
                            
                except Exception as e:
                    print(f"⚠️ Erro ao verificar navegação: {e}")
                
                return True
                
            except Exception as e:
                print(f"❌ Erro ao verificar dashboard: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste de dashboard: {e}")
            return False
    
    def test_navigation(self):
        """Testa a navegação entre páginas"""
        print("\n🧭 TESTE 4: Navegação")
        print("="*50)
        
        try:
            # Procurar links de navegação
            nav_links = self.driver.find_elements(By.XPATH, "//nav//a | //header//a | //a[contains(@class, 'nav')]")
            
            if len(nav_links) > 0:
                print(f"🔗 Testando navegação com {len(nav_links)} links...")
                
                for i, link in enumerate(nav_links[:3]):  # Testar apenas os primeiros 3 links
                    try:
                        text = link.text.strip()
                        href = link.get_attribute("href")
                        
                        if text and href and href.startswith("http"):
                            print(f"   {i+1}. Testando: {text}")
                            
                            # Clicar no link
                            link.click()
                            time.sleep(3)
                            
                            # Screenshot da página
                            self.take_screenshot(f"07_nav_{i+1}_{text.replace(' ', '_')}")
                            
                            # Verificar se a página carregou
                            current_url = self.driver.current_url
                            print(f"      URL: {current_url}")
                            
                            # Voltar para a página anterior
                            self.driver.back()
                            time.sleep(2)
                            
                    except Exception as e:
                        print(f"      ⚠️ Erro ao testar link: {e}")
                
                return True
            else:
                print("⚠️ Nenhum link de navegação encontrado")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste de navegação: {e}")
            return False
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("="*80)
        print("  🎯 TESTE END-TO-END - FINAFLOW")
        print("="*80)
        print(f"🌐 URL: {FRONTEND_URL}")
        print(f"👤 Usuário: {USERNAME}")
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*80)
        
        # Criar diretório para screenshots
        import os
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        
        if not self.setup_driver():
            return
        
        try:
            # Executar testes
            test_results = []
            
            # Teste 1: Login
            result1 = self.test_login_page()
            test_results.append(("Login", result1))
            
            if result1:
                # Teste 2: Business Unit
                result2 = self.test_business_unit_selection()
                test_results.append(("Business Unit Selection", result2))
                
                if result2:
                    # Teste 3: Dashboard
                    result3 = self.test_dashboard()
                    test_results.append(("Dashboard", result3))
                    
                    if result3:
                        # Teste 4: Navegação
                        result4 = self.test_navigation()
                        test_results.append(("Navigation", result4))
            
            # Resultados finais
            print("\n" + "="*80)
            print("  📊 RESULTADOS DOS TESTES")
            print("="*80)
            
            passed = 0
            for test_name, result in test_results:
                status = "✅ PASSOU" if result else "❌ FALHOU"
                print(f"{test_name:<25} {status}")
                if result:
                    passed += 1
            
            print("="*80)
            print(f"📈 Resultado Final: {passed}/{len(test_results)} testes passaram")
            
            if passed == len(test_results):
                print("🎉 TODOS OS TESTES PASSARAM!")
            elif passed > 0:
                print("⚠️ ALGUNS TESTES FALHARAM")
            else:
                print("❌ TODOS OS TESTES FALHARAM")
            
            print(f"📸 Screenshots salvos em: {SCREENSHOTS_DIR}/")
            print("="*80)
            
            # Salvar resultados em arquivo
            self.results["end_time"] = datetime.now().isoformat()
            self.results["test_results"] = test_results
            self.results["summary"] = {
                "total_tests": len(test_results),
                "passed": passed,
                "failed": len(test_results) - passed
            }
            
            with open("e2e_test_results.json", "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Resultados salvos em: e2e_test_results.json")
            
        except Exception as e:
            print(f"❌ Erro durante os testes: {e}")
            self.take_screenshot("error_general")
        
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Driver fechado")

def main():
    """Função principal"""
    tester = E2ETester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
