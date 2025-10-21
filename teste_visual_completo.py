#!/usr/bin/env python3
"""
🔍 TESTE VISUAL COMPLETO - SISTEMA FINAFLOW
Navegação completa via Selenium para validar todas as funcionalidades
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
from datetime import datetime

class FinaFlowTester:
    def __init__(self):
        self.driver = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }
        
    def setup_driver(self):
        """Configurar driver do Selenium"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        
    def log_test(self, test_name, status, details=""):
        """Registrar resultado do teste"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results["tests"].append(result)
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {details}")
        
    def test_frontend_access(self):
        """Testar acesso ao frontend"""
        try:
            self.driver.get("https://finaflow.vercel.app")
            time.sleep(3)
            
            # Verificar se carregou
            if "FinaFlow" in self.driver.title or "Login" in self.driver.page_source:
                self.log_test("Frontend Access", "PASS", f"Title: {self.driver.title}")
                return True
            else:
                self.log_test("Frontend Access", "FAIL", "FinaFlow not found in page")
                return False
        except Exception as e:
            self.log_test("Frontend Access", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_login(self):
        """Testar login"""
        try:
            # Procurar campos de login
            username_field = self.driver.find_element(By.NAME, "username")
            password_field = self.driver.find_element(By.NAME, "password")
            
            # Preencher credenciais
            username_field.clear()
            username_field.send_keys("lucianoterresrosa")
            password_field.clear()
            password_field.send_keys("xs95LIa9ZduX")
            
            # Clicar em login
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar') or contains(text(), 'Login')]")
            login_button.click()
            
            # Aguardar redirecionamento
            time.sleep(5)
            
            # Verificar se logou
            if "dashboard" in self.driver.current_url.lower() or "select-business-unit" in self.driver.current_url:
                self.log_test("Login", "PASS", f"Redirected to: {self.driver.current_url}")
                return True
            else:
                self.log_test("Login", "FAIL", f"Unexpected redirect: {self.driver.current_url}")
                return False
                
        except Exception as e:
            self.log_test("Login", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_business_unit_selection(self):
        """Testar seleção de business unit se necessário"""
        try:
            if "select-business-unit" in self.driver.current_url:
                # Procurar e selecionar uma business unit
                bu_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'business-unit') or contains(text(), 'LLM') or contains(text(), 'Matriz')]")
                if bu_buttons:
                    bu_buttons[0].click()
                    time.sleep(3)
                    self.log_test("Business Unit Selection", "PASS", "Selected business unit")
                else:
                    self.log_test("Business Unit Selection", "FAIL", "No business unit buttons found")
                    return False
            else:
                self.log_test("Business Unit Selection", "PASS", "Not needed - already selected")
            return True
        except Exception as e:
            self.log_test("Business Unit Selection", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_dashboard_loading(self):
        """Testar carregamento do dashboard"""
        try:
            # Ir para dashboard
            self.driver.get("https://finaflow.vercel.app/dashboard")
            time.sleep(5)
            
            # Verificar elementos do dashboard
            elements_found = []
            
            # Verificar se tem os cards principais
            if "Receita Total" in self.driver.page_source:
                elements_found.append("Receita Total")
            if "Despesas Totais" in self.driver.page_source:
                elements_found.append("Despesas Totais")
            if "Custos Totais" in self.driver.page_source:
                elements_found.append("Custos Totais")
            if "Saldo Atual" in self.driver.page_source:
                elements_found.append("Saldo Atual")
            if "Saldo Disponível" in self.driver.page_source:
                elements_found.append("Saldo Disponível")
                
            if len(elements_found) >= 4:
                self.log_test("Dashboard Loading", "PASS", f"Found elements: {', '.join(elements_found)}")
                return True
            else:
                self.log_test("Dashboard Loading", "FAIL", f"Missing elements. Found: {', '.join(elements_found)}")
                return False
                
        except Exception as e:
            self.log_test("Dashboard Loading", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_dashboard_data(self):
        """Testar se os dados estão carregando"""
        try:
            # Verificar se há valores diferentes de R$ 0,00
            page_source = self.driver.page_source
            
            # Procurar por valores monetários
            import re
            money_pattern = r'R\$\s*[\d.,]+'
            money_values = re.findall(money_pattern, page_source)
            
            # Filtrar valores diferentes de R$ 0,00
            non_zero_values = [v for v in money_values if v not in ['R$ 0,00', 'R$ 0,00', 'R$ 0,00']]
            
            if non_zero_values:
                self.log_test("Dashboard Data", "PASS", f"Found non-zero values: {non_zero_values[:5]}")
                return True
            else:
                self.log_test("Dashboard Data", "FAIL", "All values are R$ 0,00")
                return False
                
        except Exception as e:
            self.log_test("Dashboard Data", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_navigation_menu(self):
        """Testar menu de navegação"""
        try:
            menu_items = [
                "Lançamentos Financeiros",
                "Previsões Financeiras", 
                "Fluxo de Caixa Mensal",
                "Fluxo de Caixa Diário",
                "Contas Bancárias",
                "Caixa / Dinheiro",
                "Investimentos",
                "Relatórios"
            ]
            
            found_items = []
            for item in menu_items:
                if item in self.driver.page_source:
                    found_items.append(item)
                    
            if len(found_items) >= 6:
                self.log_test("Navigation Menu", "PASS", f"Found {len(found_items)} menu items")
                return True
            else:
                self.log_test("Navigation Menu", "FAIL", f"Only found {len(found_items)} menu items")
                return False
                
        except Exception as e:
            self.log_test("Navigation Menu", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_contas_bancarias_page(self):
        """Testar página de contas bancárias"""
        try:
            # Ir para página de contas bancárias
            self.driver.get("https://finaflow.vercel.app/contas-bancarias")
            time.sleep(3)
            
            # Verificar se carregou
            if "Contas Bancárias" in self.driver.page_source:
                # Verificar se tem dados
                if "CEF" in self.driver.page_source or "SICOOB" in self.driver.page_source:
                    self.log_test("Contas Bancárias Page", "PASS", "Page loaded with data")
                    return True
                else:
                    self.log_test("Contas Bancárias Page", "PASS", "Page loaded but no data visible")
                    return True
            else:
                self.log_test("Contas Bancárias Page", "FAIL", "Page not loaded properly")
                return False
                
        except Exception as e:
            self.log_test("Contas Bancárias Page", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_lancamentos_page(self):
        """Testar página de lançamentos financeiros"""
        try:
            # Ir para página de lançamentos
            self.driver.get("https://finaflow.vercel.app/transactions")
            time.sleep(3)
            
            # Verificar se carregou
            if "Lançamentos" in self.driver.page_source or "Transações" in self.driver.page_source:
                self.log_test("Lançamentos Page", "PASS", "Page loaded")
                return True
            else:
                self.log_test("Lançamentos Page", "FAIL", "Page not loaded properly")
                return False
                
        except Exception as e:
            self.log_test("Lançamentos Page", "FAIL", f"Error: {str(e)}")
            return False
            
    def take_screenshots(self):
        """Capturar screenshots"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Screenshot do dashboard
            self.driver.get("https://finaflow.vercel.app/dashboard")
            time.sleep(3)
            self.driver.save_screenshot(f"dashboard_{timestamp}.png")
            
            # Screenshot das contas bancárias
            self.driver.get("https://finaflow.vercel.app/contas-bancarias")
            time.sleep(3)
            self.driver.save_screenshot(f"contas_bancarias_{timestamp}.png")
            
            self.log_test("Screenshots", "PASS", f"Screenshots saved with timestamp {timestamp}")
            return True
            
        except Exception as e:
            self.log_test("Screenshots", "FAIL", f"Error: {str(e)}")
            return False
            
    def generate_summary(self):
        """Gerar resumo dos testes"""
        total_tests = len(self.results["tests"])
        passed_tests = len([t for t in self.results["tests"] if t["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
        }
        
        print(f"\n📊 RESUMO DOS TESTES:")
        print(f"   Total: {total_tests}")
        print(f"   ✅ Passou: {passed_tests}")
        print(f"   ❌ Falhou: {failed_tests}")
        print(f"   📈 Taxa de sucesso: {self.results['summary']['success_rate']}")
        
    def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 INICIANDO TESTES VISUAIS COMPLETOS")
        print("=" * 100)
        
        try:
            self.setup_driver()
            
            # Executar testes em sequência
            tests = [
                self.test_frontend_access,
                self.test_login,
                self.test_business_unit_selection,
                self.test_dashboard_loading,
                self.test_dashboard_data,
                self.test_navigation_menu,
                self.test_contas_bancarias_page,
                self.test_lancamentos_page,
                self.take_screenshots
            ]
            
            for test in tests:
                test()
                time.sleep(2)
                
            self.generate_summary()
            
            # Salvar resultados
            with open(f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                json.dump(self.results, f, indent=2)
                
            return self.results["summary"]["success_rate"]
            
        except Exception as e:
            print(f"❌ Erro geral: {str(e)}")
            return "0%"
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    tester = FinaFlowTester()
    success_rate = tester.run_all_tests()
    print(f"\n🎯 RESULTADO FINAL: {success_rate}")
