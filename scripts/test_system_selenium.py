#!/usr/bin/env python3
"""
Script Selenium para testar automaticamente o sistema finaFlow
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FinaFlowSeleniumTester:
    def __init__(self):
        self.driver = None
        self.base_url = "https://finaflow.vercel.app"
        self.results = {
            "middleware_protection": False,
            "login_redirect": False,
            "login_working": False,
            "dashboard_access": False,
            "menu_portuguese": False,
            "protected_routes": False,
            "logout_working": False
        }
        
    def setup_driver(self):
        """Configura o driver do Chrome"""
        print("🔧 Configurando driver do Chrome...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def test_middleware_protection(self):
        """Testa se o middleware está protegendo as rotas"""
        print("\n🔒 Testando proteção do middleware...")
        
        try:
            # Tentar acessar dashboard sem login
            self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(5)
            
            current_url = self.driver.current_url
            print(f"   URL atual: {current_url}")
            
            if "/login" in current_url:
                print("   ✅ Middleware redirecionou para login")
                self.results["middleware_protection"] = True
                self.results["login_redirect"] = True
            else:
                print("   ❌ Middleware não redirecionou")
                
        except Exception as e:
            print(f"   ❌ Erro ao testar middleware: {e}")
            
    def test_login(self):
        """Testa o login"""
        print("\n🔐 Testando login...")
        
        try:
            # Verificar se já estamos na página de login
            if "/login" not in self.driver.current_url:
                self.driver.get(f"{self.base_url}/login")
                time.sleep(3)
            
            # Preencher formulário
            username_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            username_input.clear()
            username_input.send_keys("admin")
            password_input.clear()
            password_input.send_keys("admin123")
            
            # Clicar no botão de login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Aguardar redirecionamento
            time.sleep(8)
            
            current_url = self.driver.current_url
            print(f"   URL após login: {current_url}")
            
            if "/dashboard" in current_url:
                print("   ✅ Login bem-sucedido, redirecionou para dashboard")
                self.results["login_working"] = True
                self.results["dashboard_access"] = True
            else:
                print("   ❌ Login falhou ou não redirecionou")
                
        except Exception as e:
            print(f"   ❌ Erro no login: {e}")
            
    def test_menu_portuguese(self):
        """Testa se o menu está em português"""
        print("\n🇧🇷 Testando menu em português...")
        
        try:
            # Verificar se estamos no dashboard
            if "/dashboard" not in self.driver.current_url:
                print("   ⚠️ Não está no dashboard, pulando teste do menu")
                return
                
            # Aguardar carregamento do menu
            time.sleep(3)
            
            # Verificar itens do menu
            menu_items = self.driver.find_elements(By.CSS_SELECTOR, "nav a, .sidebar a")
            
            portuguese_items = [
                "Dashboard", "Contas", "Transações", "Grupos", "Subgrupos", 
                "Previsões", "Relatórios", "Importar CSV", "Usuários", "Configurações"
            ]
            
            found_items = []
            for item in menu_items:
                text = item.text.strip()
                if text and len(text) > 1:
                    found_items.append(text)
                    
            print(f"   Itens encontrados no menu: {found_items}")
            
            # Verificar se há itens em português
            portuguese_count = sum(1 for item in found_items if item in portuguese_items)
            
            if portuguese_count >= 5:  # Pelo menos 5 itens em português
                print("   ✅ Menu está em português")
                self.results["menu_portuguese"] = True
            else:
                print("   ❌ Menu não está em português")
                
        except Exception as e:
            print(f"   ❌ Erro ao testar menu: {e}")
            
    def test_protected_routes(self):
        """Testa outras rotas protegidas após login"""
        print("\n🛡️ Testando rotas protegidas após login...")
        
        protected_routes = ["/accounts", "/transactions", "/groups", "/users"]
        accessible_routes = 0
        
        for route in protected_routes:
            try:
                self.driver.get(f"{self.base_url}{route}")
                time.sleep(3)
                
                current_url = self.driver.current_url
                print(f"   {route}: {current_url}")
                
                if route in current_url:
                    print(f"   ✅ {route} acessível após login")
                    accessible_routes += 1
                elif "/login" in current_url:
                    print(f"   ❌ {route} redirecionou para login (mesmo logado)")
                else:
                    print(f"   ⚠️ {route} comportamento inesperado")
                    
            except Exception as e:
                print(f"   ❌ Erro ao testar {route}: {e}")
        
        if accessible_routes >= 3:
            print("   ✅ Maioria das rotas protegidas funcionando")
            self.results["protected_routes"] = True
        else:
            print("   ❌ Problemas com rotas protegidas")
            
    def test_logout(self):
        """Testa o logout"""
        print("\n🚪 Testando logout...")
        
        try:
            # Procurar botão de logout
            logout_selectors = [
                "button[onclick*='logout']",
                "button:contains('Logout')",
                "a[href*='logout']",
                ".logout",
                "[data-testid='logout']"
            ]
            
            logout_button = None
            for selector in logout_selectors:
                try:
                    logout_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if logout_button:
                logout_button.click()
                time.sleep(3)
                
                current_url = self.driver.current_url
                if "/login" in current_url:
                    print("   ✅ Logout funcionou, redirecionou para login")
                    self.results["logout_working"] = True
                else:
                    print("   ❌ Logout não redirecionou para login")
            else:
                print("   ⚠️ Botão de logout não encontrado")
                
        except Exception as e:
            print(f"   ❌ Erro no logout: {e}")
            
    def test_route_protection_after_logout(self):
        """Testa se as rotas ficam protegidas após logout"""
        print("\n🔒 Testando proteção após logout...")
        
        try:
            # Tentar acessar dashboard após logout
            self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(3)
            
            current_url = self.driver.current_url
            if "/login" in current_url:
                print("   ✅ Rotas protegidas após logout")
                self.results["middleware_protection"] = True
            else:
                print("   ❌ Rotas não protegidas após logout")
                
        except Exception as e:
            print(f"   ❌ Erro ao testar proteção após logout: {e}")
            
    def generate_report(self):
        """Gera relatório dos testes"""
        print("\n" + "="*60)
        print("📋 RELATÓRIO COMPLETO DOS TESTES SELENIUM")
        print("="*60)
        
        for test, result in self.results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            test_name = test.replace('_', ' ').title()
            print(f"{test_name}: {status}")
            
        print("\n" + "="*60)
        
        # Resumo
        passed = sum(self.results.values())
        total = len(self.results)
        
        print(f"RESULTADO: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 SISTEMA FUNCIONANDO PERFEITAMENTE!")
        elif passed >= total * 0.8:
            print("✅ SISTEMA FUNCIONAL COM PEQUENOS AJUSTES")
        elif passed >= total * 0.6:
            print("⚠️ SISTEMA PARCIALMENTE FUNCIONAL")
        else:
            print("❌ SISTEMA COM PROBLEMAS CRÍTICOS")
            
        # Salvar relatório
        with open('selenium_test_report.json', 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'results': self.results,
                'summary': {
                    'passed': passed,
                    'total': total,
                    'percentage': (passed/total)*100
                }
            }, f, indent=2)
            
        print(f"\n📄 Relatório salvo em: selenium_test_report.json")
            
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 INICIANDO TESTES SELENIUM DO FINAFLOW")
        print("="*60)
        
        try:
            self.setup_driver()
            
            # Teste 1: Proteção do middleware
            self.test_middleware_protection()
            
            # Teste 2: Login
            self.test_login()
            
            # Teste 3: Menu em português
            self.test_menu_portuguese()
            
            # Teste 4: Rotas protegidas após login
            self.test_protected_routes()
            
            # Teste 5: Logout
            self.test_logout()
            
            # Teste 6: Proteção após logout
            self.test_route_protection_after_logout()
            
            # Gerar relatório
            self.generate_report()
            
        except Exception as e:
            print(f"❌ Erro geral nos testes: {e}")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    tester = FinaFlowSeleniumTester()
    tester.run_all_tests()
