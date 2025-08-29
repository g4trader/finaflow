#!/usr/bin/env python3
"""
PLANO PROFISSIONAL DE QA - FinaFlow
Testes automatizados com Selenium para validação real do sistema
"""

import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import requests

class FinaFlowQATest(unittest.TestCase):
    """Testes automatizados para o sistema FinaFlow"""
    
    def setUp(self):
        """Configuração inicial do ambiente de teste"""
        print("🔧 Configurando ambiente de teste...")
        
        # Configurações do Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Inicializar driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # URLs do sistema
        self.frontend_url = "https://finaflow.vercel.app"
        self.backend_url = "https://finaflow-backend-609095880025.us-central1.run.app"
        
        # Credenciais de teste
        self.test_credentials = {
            "username": "admin",
            "password": "test"
        }
        
        print("✅ Ambiente configurado com sucesso")

    def tearDown(self):
        """Limpeza após os testes"""
        if hasattr(self, 'driver'):
            self.driver.quit()
        print("🧹 Ambiente limpo")

    def test_01_backend_health_check(self):
        """Teste 1: Verificar se o backend está respondendo"""
        print("\n🔍 Teste 1: Verificação de saúde do backend")
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            self.assertEqual(response.status_code, 200)
            print("✅ Backend respondendo corretamente")
            
            response = requests.get(f"{self.backend_url}/api/v1/auth/users", timeout=10)
            self.assertEqual(response.status_code, 200)
            users_data = response.json()
            self.assertIsInstance(users_data, list)
            print(f"✅ Endpoint de usuários funcionando - {len(users_data)} usuários encontrados")
            
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ Backend não está respondendo: {e}")

    def test_02_frontend_accessibility(self):
        """Teste 2: Verificar se o frontend está acessível"""
        print("\n🔍 Teste 2: Acessibilidade do frontend")
        
        try:
            self.driver.get(f"{self.frontend_url}/login")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            title = self.driver.title
            self.assertIn("FinaFlow", title)
            print(f"✅ Frontend acessível - Título: {title}")
            
        except TimeoutException:
            self.fail("❌ Frontend não carregou dentro do tempo limite")

    def test_03_login_functionality(self):
        """Teste 3: Testar funcionalidade de login"""
        print("\n🔍 Teste 3: Funcionalidade de login")
        
        try:
            self.driver.get(f"{self.frontend_url}/login")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.clear()
            username_field.send_keys(self.test_credentials["username"])
            
            password_field.clear()
            password_field.send_keys(self.test_credentials["password"])
            
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
            login_button.click()
            
            self.wait.until(EC.url_contains("dashboard"))
            print("✅ Login realizado com sucesso")
            
        except (TimeoutException, NoSuchElementException) as e:
            self.fail(f"❌ Falha no login: {e}")

    def test_04_users_page_navigation(self):
        """Teste 4: Navegação para página de usuários"""
        print("\n🔍 Teste 4: Navegação para página de usuários")
        
        try:
            self.test_03_login_functionality()
            time.sleep(2)
            
            # Procurar por diferentes seletores para o link de usuários
            users_link = None
            selectors = [
                "//a[contains(text(), 'Usuários')]",
                "//a[contains(text(), 'Users')]",
                "//a[@href='/users']",
                "//a[contains(@href, 'users')]"
            ]
            
            for selector in selectors:
                try:
                    users_link = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"   ✅ Link de usuários encontrado com seletor: {selector}")
                    break
                except:
                    continue
            
            if not users_link:
                self.fail("❌ Link de usuários não encontrado com nenhum seletor")
            users_link.click()
            
            self.wait.until(EC.url_contains("users"))
            print("✅ Navegação para página de usuários bem-sucedida")
            
        except (TimeoutException, NoSuchElementException) as e:
            self.fail(f"❌ Falha na navegação para usuários: {e}")

    def test_05_users_page_loading(self):
        """Teste 5: Carregamento da página de usuários"""
        print("\n🔍 Teste 5: Carregamento da página de usuários")
        
        try:
            self.test_04_users_page_navigation()
            
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Usuários')]"))
            )
            
            users_table = self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            print("✅ Página de usuários carregada corretamente")
            
            table_rows = users_table.find_elements(By.TAG_NAME, "tr")
            self.assertGreater(len(table_rows), 1)
            print(f"✅ Tabela de usuários com {len(table_rows)-1} registros")
            
        except (TimeoutException, NoSuchElementException) as e:
            self.fail(f"❌ Falha no carregamento da página de usuários: {e}")

    def test_06_create_user_form(self):
        """Teste 6: Testar formulário de criação de usuário"""
        print("\n🔍 Teste 6: Formulário de criação de usuário")
        
        try:
            self.test_05_users_page_loading()
            
            new_user_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Novo Usuário')]"))
            )
            new_user_button.click()
            
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Novo Usuário')]"))
            )
            print("✅ Modal de criação de usuário aberto")
            
            form_fields = {
                "name": "Teste QA",
                "email": "teste.qa@empresa.com",
                "phone": "(11) 12345-6789"
            }
            
            for field_name, field_value in form_fields.items():
                try:
                    field = self.driver.find_element(By.NAME, field_name)
                    field.clear()
                    field.send_keys(field_value)
                    time.sleep(0.5)
                    
                    actual_value = field.get_attribute("value")
                    self.assertEqual(actual_value, field_value)
                    print(f"✅ Campo {field_name} funcionando corretamente")
                    
                except NoSuchElementException:
                    print(f"⚠️ Campo {field_name} não encontrado")
            
            print("✅ Formulário preenchido com sucesso")
            
        except (TimeoutException, NoSuchElementException) as e:
            self.fail(f"❌ Falha no formulário de criação: {e}")

    def test_07_form_field_focus_issue(self):
        """Teste 7: Verificar problema de perda de foco nos campos"""
        print("\n🔍 Teste 7: Verificação de perda de foco nos campos")
        
        try:
            self.test_06_create_user_form()
            
            name_field = self.driver.find_element(By.NAME, "name")
            name_field.click()
            name_field.clear()
            
            test_text = "Teste de digitação contínua"
            for char in test_text:
                name_field.send_keys(char)
                time.sleep(0.1)
                
                focused_element = self.driver.switch_to.active_element
                if focused_element != name_field:
                    self.fail(f"❌ Campo perdeu foco após digitar '{char}'")
            
            print("✅ Campo mantém foco durante digitação")
            
        except (TimeoutException, NoSuchElementException) as e:
            self.fail(f"❌ Falha no teste de foco: {e}")

def run_qa_tests():
    """Executar todos os testes de QA"""
    print("🚀 INICIANDO TESTES PROFISSIONAIS DE QA - FinaFlow")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(FinaFlowQATest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DE QA")
    print("=" * 60)
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"⚠️ Erros: {len(result.errors)}")
    
    if result.failures:
        print("\n🔍 DETALHES DAS FALHAS:")
        for test, traceback in result.failures:
            print(f"\n❌ {test}:")
            print(traceback)
    
    if result.errors:
        print("\n🔍 DETALHES DOS ERROS:")
        for test, traceback in result.errors:
            print(f"\n⚠️ {test}:")
            print(traceback)
    
    if result.wasSuccessful():
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM - NECESSÁRIO CORREÇÃO")
        return False

if __name__ == "__main__":
    success = run_qa_tests()
    exit(0 if success else 1)
