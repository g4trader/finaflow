#!/usr/bin/env python3
"""
Script para testar automaticamente o sistema finaFlow
"""

import requests
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

class FinaFlowTester:
    def __init__(self):
        self.driver = None
        self.base_url = "https://finaflow.vercel.app"
        self.results = {
            "route_protection": False,
            "menu_portuguese": False,
            "login_working": False,
            "dashboard_data": False,
            "redirects": False
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
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def test_route_protection(self):
        """Testa se as rotas estão protegidas"""
        print("\n🔒 Testando proteção de rotas...")
        
        try:
            # Tentar acessar dashboard sem login
            self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(3)
            
            current_url = self.driver.current_url
            print(f"   URL atual: {current_url}")
            
            if "/login" in current_url:
                print("   ✅ Dashboard redirecionou para login")
                self.results["route_protection"] = True
                self.results["redirects"] = True
            else:
                print("   ❌ Dashboard não redirecionou para login")
                self.results["route_protection"] = False
                
        except Exception as e:
            print(f"   ❌ Erro ao testar proteção: {e}")
            
    def test_login(self):
        """Testa o login"""
        print("\n🔐 Testando login...")
        
        try:
            # Ir para página de login
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            # Preencher formulário
            username_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            username_input.send_keys("admin")
            password_input.send_keys("admin123")
            
            # Clicar no botão de login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Aguardar redirecionamento
            time.sleep(5)
            
            current_url = self.driver.current_url
            print(f"   URL após login: {current_url}")
            
            if "/dashboard" in current_url:
                print("   ✅ Login bem-sucedido, redirecionou para dashboard")
                self.results["login_working"] = True
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
                
            # Verificar itens do menu
            menu_items = self.driver.find_elements(By.CSS_SELECTOR, "nav a")
            
            portuguese_items = [
                "Dashboard", "Contas", "Transações", "Grupos", "Subgrupos", 
                "Previsões", "Relatórios", "Importar CSV", "Usuários", "Configurações"
            ]
            
            found_items = []
            for item in menu_items:
                text = item.text.strip()
                if text:
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
            
    def test_dashboard_data(self):
        """Testa se o dashboard carrega dados reais"""
        print("\n📊 Testando dados do dashboard...")
        
        try:
            # Aguardar carregamento
            time.sleep(3)
            
            # Verificar se há loading states
            loading_elements = self.driver.find_elements(By.CSS_SELECTOR, ".animate-pulse")
            
            if loading_elements:
                print("   ⚠️ Dashboard ainda em loading")
                self.results["dashboard_data"] = False
            else:
                # Verificar se há dados reais
                metric_cards = self.driver.find_elements(By.CSS_SELECTOR, ".text-2xl.font-bold")
                
                if metric_cards:
                    print("   ✅ Dashboard carregou dados")
                    self.results["dashboard_data"] = True
                else:
                    print("   ❌ Dashboard não carregou dados")
                    
        except Exception as e:
            print(f"   ❌ Erro ao testar dados: {e}")
            
    def test_other_protected_routes(self):
        """Testa outras rotas protegidas"""
        print("\n🛡️ Testando outras rotas protegidas...")
        
        protected_routes = ["/accounts", "/transactions", "/groups", "/users"]
        
        for route in protected_routes:
            try:
                self.driver.get(f"{self.base_url}{route}")
                time.sleep(2)
                
                current_url = self.driver.current_url
                print(f"   {route}: {current_url}")
                
                if "/login" in current_url:
                    print(f"   ✅ {route} protegida corretamente")
                else:
                    print(f"   ❌ {route} não está protegida")
                    
            except Exception as e:
                print(f"   ❌ Erro ao testar {route}: {e}")
                
    def generate_report(self):
        """Gera relatório dos testes"""
        print("\n" + "="*50)
        print("📋 RELATÓRIO DOS TESTES")
        print("="*50)
        
        for test, result in self.results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{test.replace('_', ' ').title()}: {status}")
            
        print("\n" + "="*50)
        
        # Resumo
        passed = sum(self.results.values())
        total = len(self.results)
        
        print(f"RESULTADO: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 SISTEMA FUNCIONANDO PERFEITAMENTE!")
        elif passed >= total * 0.7:
            print("⚠️ SISTEMA PARCIALMENTE FUNCIONAL")
        else:
            print("❌ SISTEMA COM PROBLEMAS CRÍTICOS")
            
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 INICIANDO TESTES AUTOMATIZADOS DO FINAFLOW")
        print("="*50)
        
        try:
            self.setup_driver()
            
            # Teste 1: Proteção de rotas
            self.test_route_protection()
            
            # Teste 2: Login
            self.test_login()
            
            # Teste 3: Menu em português
            self.test_menu_portuguese()
            
            # Teste 4: Dados do dashboard
            self.test_dashboard_data()
            
            # Teste 5: Outras rotas protegidas
            self.test_other_protected_routes()
            
            # Gerar relatório
            self.generate_report()
            
        except Exception as e:
            print(f"❌ Erro geral nos testes: {e}")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    tester = FinaFlowTester()
    tester.run_all_tests()
