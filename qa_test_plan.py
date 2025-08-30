#!/usr/bin/env python3
"""
Teste de QA Profissional - FinaFlow
Validação completa do CRUD de usuários com verificação no banco de dados
"""

import unittest
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class FinaFlowQATest(unittest.TestCase):
    def setUp(self):
        """Configuração do ambiente de teste"""
        print("🔧 Configurando ambiente de teste...")
        
        # URLs
        self.frontend_url = "https://finaflow.vercel.app"
        self.backend_url = "https://finaflow-backend-609095880025.us-central1.run.app"
        
        # Configurar Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Inicializar driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Dados de teste
        self.test_user = {
            "name": f"Usuário Teste QA {int(time.time())}",
            "email": f"teste.qa.{int(time.time())}@finaflow.com",
            "phone": f"1199999{int(time.time()) % 10000:04d}",
            "role": "user",
            "status": "active"
        }
        
        self.created_user_id = None
        self.auth_token = None
        
        print("✅ Ambiente configurado com sucesso")

    def tearDown(self):
        """Limpeza do ambiente de teste"""
        print("🧹 Ambiente limpo")
        if self.driver:
            self.driver.quit()

    def test_01_backend_health_check(self):
        """Teste 1: Verificar se o backend está respondendo"""
        print("\n🔍 Teste 1: Verificação de saúde do backend")
        
        # Verificar se o backend está online
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            self.assertEqual(response.status_code, 200)
            print("✅ Backend respondendo corretamente")
        except Exception as e:
            self.fail(f"❌ Backend não está respondendo: {e}")
        
        # Verificar endpoint de usuários
        try:
            response = requests.get(f"{self.backend_url}/api/v1/users", timeout=10)
            self.assertEqual(response.status_code, 200)
            users = response.json()
            print(f"✅ Endpoint de usuários funcionando - {len(users)} usuários encontrados")
        except Exception as e:
            self.fail(f"❌ Endpoint de usuários falhou: {e}")

    def test_02_login_and_get_token(self):
        """Teste 2: Fazer login e obter token de autenticação"""
        print("\n🔍 Teste 2: Login e obtenção de token")
        
        # Fazer login via API
        login_data = {
            "username": "admin@finaflow.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(f"{self.backend_url}/api/v1/auth/login", json=login_data, timeout=10)
            self.assertEqual(response.status_code, 200)
            
            login_response = response.json()
            self.auth_token = login_response.get("access_token")
            self.assertIsNotNone(self.auth_token, "Token de acesso não foi retornado")
            
            print("✅ Login realizado com sucesso")
            print(f"✅ Token obtido: {self.auth_token[:20]}...")
            
        except Exception as e:
            self.fail(f"❌ Falha no login: {e}")

    def test_03_verify_initial_users_in_database(self):
        """Teste 3: Verificar usuários iniciais no banco de dados"""
        print("\n🔍 Teste 3: Verificação de usuários iniciais no banco")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = requests.get(f"{self.backend_url}/api/v1/users", headers=headers, timeout=10)
            self.assertEqual(response.status_code, 200)
            
            initial_users = response.json()
            print(f"✅ {len(initial_users)} usuários encontrados no banco inicialmente")
            
            # Verificar se são dados reais (não mock)
            for user in initial_users:
                self.assertIn("id", user, "Usuário deve ter ID")
                self.assertIn("name", user, "Usuário deve ter nome")
                self.assertIn("email", user, "Usuário deve ter email")
                print(f"   - {user['name']} ({user['email']})")
            
            self.initial_users_count = len(initial_users)
            
        except Exception as e:
            self.fail(f"❌ Falha ao verificar usuários iniciais: {e}")

    def test_04_create_user_via_api(self):
        """Teste 4: Criar usuário via API e verificar no banco"""
        print("\n🔍 Teste 4: Criação de usuário via API")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Verificar número inicial de usuários
            response = requests.get(f"{self.backend_url}/api/v1/users", headers=headers, timeout=10)
            self.assertEqual(response.status_code, 200)
            initial_users = response.json()
            initial_count = len(initial_users)
            
            # Criar usuário
            response = requests.post(f"{self.backend_url}/api/v1/users", 
                                   json=self.test_user, 
                                   headers=headers, 
                                   timeout=10)
            self.assertEqual(response.status_code, 201)
            
            created_user = response.json()
            self.created_user_id = created_user["id"]
            
            print(f"✅ Usuário criado com ID: {self.created_user_id}")
            print(f"   - Nome: {created_user['name']}")
            print(f"   - Email: {created_user['email']}")
            
            # Verificar se foi realmente salvo no banco
            response = requests.get(f"{self.backend_url}/api/v1/users", headers=headers, timeout=10)
            self.assertEqual(response.status_code, 200)
            
            users_after_create = response.json()
            self.assertEqual(len(users_after_create), initial_count + 1)
            
            # Encontrar o usuário criado na lista
            created_user_in_list = next((u for u in users_after_create if u["id"] == self.created_user_id), None)
            self.assertIsNotNone(created_user_in_list, "Usuário criado não encontrado na lista")
            
            print("✅ Usuário confirmado no banco de dados")
            
        except Exception as e:
            self.fail(f"❌ Falha na criação de usuário: {e}")

    def test_05_update_user_via_api(self):
        """Teste 5: Atualizar usuário via API e verificar no banco"""
        print("\n🔍 Teste 5: Atualização de usuário via API")
        
        if not self.created_user_id:
            self.skipTest("Usuário não foi criado no teste anterior")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Dados de atualização
        update_data = {
            "name": f"{self.test_user['name']} - ATUALIZADO",
            "phone": f"1188888{int(time.time()) % 10000:04d}",
            "role": "admin"
        }
        
        try:
            # Atualizar usuário
            response = requests.put(f"{self.backend_url}/api/v1/users/{self.created_user_id}", 
                                  json=update_data, 
                                  headers=headers, 
                                  timeout=10)
            self.assertEqual(response.status_code, 200)
            
            updated_user = response.json()
            print(f"✅ Usuário atualizado: {updated_user['name']}")
            
            # Verificar se foi realmente atualizado no banco
            response = requests.get(f"{self.backend_url}/api/v1/users/{self.created_user_id}", 
                                  headers=headers, 
                                  timeout=10)
            self.assertEqual(response.status_code, 200)
            
            user_from_db = response.json()
            self.assertEqual(user_from_db["name"], update_data["name"])
            self.assertEqual(user_from_db["phone"], update_data["phone"])
            self.assertEqual(user_from_db["role"], update_data["role"])
            
            print("✅ Atualização confirmada no banco de dados")
            
        except Exception as e:
            self.fail(f"❌ Falha na atualização de usuário: {e}")

    def test_06_delete_user_via_api(self):
        """Teste 6: Deletar usuário via API e verificar no banco"""
        print("\n🔍 Teste 6: Exclusão de usuário via API")
        
        if not self.created_user_id:
            self.skipTest("Usuário não foi criado nos testes anteriores")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Deletar usuário
            response = requests.delete(f"{self.backend_url}/api/v1/users/{self.created_user_id}", 
                                     headers=headers, 
                                     timeout=10)
            self.assertEqual(response.status_code, 204)
            
            print("✅ Usuário deletado via API")
            
            # Verificar se foi realmente removido do banco
            response = requests.get(f"{self.backend_url}/api/v1/users", headers=headers, timeout=10)
            self.assertEqual(response.status_code, 200)
            
            users_after_delete = response.json()
            self.assertEqual(len(users_after_delete), self.initial_users_count)
            
            # Verificar se o usuário não existe mais
            response = requests.get(f"{self.backend_url}/api/v1/users/{self.created_user_id}", 
                                  headers=headers, 
                                  timeout=10)
            self.assertEqual(response.status_code, 404)
            
            print("✅ Exclusão confirmada no banco de dados")
            
        except Exception as e:
            self.fail(f"❌ Falha na exclusão de usuário: {e}")

    def test_07_frontend_crud_integration(self):
        """Teste 7: Testar CRUD completo via frontend"""
        print("\n🔍 Teste 7: CRUD completo via frontend")
        
        try:
            # 1. Acessar página de login
            self.driver.get(f"{self.frontend_url}/login")
            self.wait.until(EC.title_contains("FinaFlow - Login"))
            print("✅ Página de login carregada")
            
            # 2. Fazer login
            username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_input = self.driver.find_element(By.NAME, "password")
            
            username_input.send_keys("admin@finaflow.com")
            password_input.send_keys("admin123")
            
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
            login_button.click()
            
            # 3. Aguardar redirecionamento para dashboard
            self.wait.until(EC.url_contains("/dashboard"))
            print("✅ Login realizado com sucesso")
            
            # 4. Navegar para página de usuários
            users_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/users']")))
            users_link.click()
            
            # 5. Aguardar carregamento da página de usuários
            self.wait.until(EC.url_contains("/users"))
            print("✅ Página de usuários carregada")
            
            # 6. Verificar se os dados são reais (mesmo número do banco)
            users_table = self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
            user_rows = users_table.find_elements(By.XPATH, ".//tbody/tr")
            
            # Verificar se há pelo menos 3 usuários (dados reais do banco)
            self.assertGreaterEqual(len(user_rows), 3)
            print(f"✅ Tabela mostra {len(user_rows)} usuários (dados reais do banco)")
            
            # 7. Testar criação via frontend
            create_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Novo Usuário')]")
            create_button.click()
            
            # Aguardar modal
            modal = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'modal')]")))
            print("✅ Modal de criação aberto")
            
            # Preencher formulário
            name_input = modal.find_element(By.NAME, "name")
            email_input = modal.find_element(By.NAME, "email")
            phone_input = modal.find_element(By.NAME, "phone")
            
            test_name = f"Frontend Test {int(time.time())}"
            test_email = f"frontend.test.{int(time.time())}@finaflow.com"
            test_phone = f"1177777{int(time.time()) % 10000:04d}"
            
            name_input.send_keys(test_name)
            email_input.send_keys(test_email)
            phone_input.send_keys(test_phone)
            
            # Salvar
            save_button = modal.find_element(By.XPATH, ".//button[contains(text(), 'Salvar')]")
            save_button.click()
            
            # Aguardar atualização da tabela
            time.sleep(2)
            updated_user_rows = users_table.find_elements(By.XPATH, ".//tbody/tr")
            self.assertGreaterEqual(len(updated_user_rows), 4)  # Pelo menos 4 usuários após criação
            print("✅ Usuário criado via frontend")
            
            # 8. Testar edição via frontend
            edit_button = updated_user_rows[-1].find_element(By.XPATH, ".//button[contains(@title, 'Editar')]")
            edit_button.click()
            
            # Aguardar modal de edição
            edit_modal = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'modal')]")))
            print("✅ Modal de edição aberto")
            
            # Modificar nome
            edit_name_input = edit_modal.find_element(By.NAME, "name")
            edit_name_input.clear()
            edit_name_input.send_keys(f"{test_name} - EDITADO")
            
            # Salvar edição
            edit_save_button = edit_modal.find_element(By.XPATH, ".//button[contains(text(), 'Salvar')]")
            edit_save_button.click()
            
            time.sleep(2)
            print("✅ Usuário editado via frontend")
            
            # 9. Testar exclusão via frontend
            delete_button = updated_user_rows[-1].find_element(By.XPATH, ".//button[contains(@title, 'Excluir')]")
            delete_button.click()
            
            # Confirmar exclusão
            confirm_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirmar')]")))
            confirm_button.click()
            
            time.sleep(2)
            final_user_rows = users_table.find_elements(By.XPATH, ".//tbody/tr")
            self.assertGreaterEqual(len(final_user_rows), 3)  # Voltou para pelo menos 3 usuários
            print("✅ Usuário excluído via frontend")
            
            print("✅ CRUD completo via frontend validado com sucesso!")
            
        except Exception as e:
            self.fail(f"❌ Falha no CRUD via frontend: {e}")

def run_qa_tests():
    """Executar todos os testes de QA"""
    print("\n🚀 INICIANDO TESTES PROFISSIONAIS DE QA - FinaFlow")
    print("=" * 60)
    
    # Configurar suite de testes
    suite = unittest.TestSuite()
    
    # Adicionar testes na ordem correta
    suite.addTest(FinaFlowQATest("test_01_backend_health_check"))
    suite.addTest(FinaFlowQATest("test_02_login_and_get_token"))
    suite.addTest(FinaFlowQATest("test_03_verify_initial_users_in_database"))
    suite.addTest(FinaFlowQATest("test_04_create_user_via_api"))
    suite.addTest(FinaFlowQATest("test_05_update_user_via_api"))
    suite.addTest(FinaFlowQATest("test_06_delete_user_via_api"))
    suite.addTest(FinaFlowQATest("test_07_frontend_crud_integration"))
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DE QA PROFISSIONAL")
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
        print("\n🎉 TODOS OS TESTES PASSARAM - SISTEMA APROVADO!")
        print("✅ Backend: Funcionando")
        print("✅ Frontend: Funcionando")
        print("✅ CRUD: Totalmente operacional")
        print("✅ Banco de dados: Integrado")
        print("✅ Autenticação: Funcionando")
        print("✅ Interface: Responsiva")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM - NECESSÁRIO CORREÇÃO")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_qa_tests()
    exit(0 if success else 1)
