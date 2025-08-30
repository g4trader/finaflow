#!/usr/bin/env python3
"""
Teste específico para verificar problema do telefone e salvamento no banco
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_phone_and_database():
    """Testa especificamente o problema do telefone e salvamento no banco"""
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🧪 Testando problema do telefone e salvamento no banco...")
        
        # 1. Verificar estado inicial do banco
        print("1. Verificando estado inicial do banco...")
        response = requests.get("https://finaflow-backend-609095880025.us-central1.run.app/api/v1/users")
        initial_users = response.json()
        print(f"   Usuários iniciais no banco: {len(initial_users)}")
        
        # 2. Login
        print("2. Fazendo login...")
        driver.get("https://finaflow.vercel.app/login")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin@finaflow.com")
        password_field.send_keys("admin123")
        
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
        login_button.click()
        
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        print("✅ Login realizado")
        
        # 3. Navegar para usuários
        print("3. Navegando para página de usuários...")
        driver.get("https://finaflow.vercel.app/users")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Página de usuários carregada")
        
        # 4. Abrir modal
        print("4. Abrindo modal...")
        novo_usuario_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Novo Usuário')]")
        novo_usuario_btn.click()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Modal aberto")
        
        # 5. Preencher formulário
        print("5. Preenchendo formulário...")
        
        # Nome
        nome_field = driver.find_element(By.XPATH, "//input[@placeholder='Digite o nome']")
        nome_field.send_keys("Teste Telefone")
        
        # Email
        email_field = driver.find_element(By.XPATH, "//input[@placeholder='email@exemplo.com']")
        email_field.send_keys("teste.telefone@exemplo.com")
        
        # Telefone - digitar número sem formatação
        telefone_field = driver.find_element(By.XPATH, "//input[@placeholder='(11) 99999-9999']")
        telefone_field.clear()
        telefone_field.send_keys("11987654321")  # Número diferente para teste
        time.sleep(1)
        
        valor_telefone_campo = telefone_field.get_attribute("value")
        print(f"   Valor do telefone no campo: '{valor_telefone_campo}'")
        
        # 6. Capturar requisição de rede
        print("6. Capturando requisição de rede...")
        
        # Ativar logs de rede
        driver.execute_script("window.performance.setResourceTimingBufferSize(1000);")
        
        # Clicar no botão de criar
        criar_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Criar')]")
        criar_btn.click()
        
        # Aguardar modal fechar
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//h3[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Usuário criado")
        
        # 7. Verificar logs de rede
        print("7. Verificando logs de rede...")
        logs = driver.get_log('performance')
        
        # Procurar por requisições POST para /api/v1/users
        for log in logs:
            if 'message' in log:
                message = log['message']
                if 'POST' in message and '/api/v1/users' in message:
                    print(f"   Requisição encontrada: {message}")
        
        # 8. Verificar se usuário aparece na lista do frontend
        print("8. Verificando se usuário aparece na lista...")
        time.sleep(2)
        
        try:
            usuario_criado = driver.find_element(By.XPATH, "//td[contains(text(), 'Teste Telefone')]")
            print("✅ Usuário encontrado na lista do frontend")
            
            # Verificar telefone na lista
            try:
                telefone_na_lista = driver.find_element(By.XPATH, "//td[contains(text(), '11987654321')]")
                print("✅ Telefone correto na lista (sem máscara)")
            except:
                try:
                    telefone_na_lista = driver.find_element(By.XPATH, "//td[contains(text(), '(11) 98765-4321')]")
                    print("✅ Telefone formatado na lista (com máscara)")
                except:
                    print("❌ Telefone não encontrado na lista")
                    
        except:
            print("❌ Usuário não encontrado na lista do frontend")
        
        # 9. Verificar se usuário foi salvo no banco
        print("9. Verificando se usuário foi salvo no banco...")
        time.sleep(3)  # Aguardar um pouco mais
        
        response = requests.get("https://finaflow-backend-609095880025.us-central1.run.app/api/v1/users")
        final_users = response.json()
        print(f"   Usuários finais no banco: {len(final_users)}")
        
        # Procurar pelo usuário criado
        test_user = None
        for user in final_users:
            if user.get('email') == 'teste.telefone@exemplo.com':
                test_user = user
                break
        
        if test_user:
            print("✅ Usuário encontrado no banco de dados")
            print(f"   Nome: {test_user.get('name')}")
            print(f"   Email: {test_user.get('email')}")
            print(f"   Telefone: {test_user.get('phone')}")
            
            # Verificar se o telefone está correto
            if test_user.get('phone') == '11987654321':
                print("✅ Telefone salvo corretamente (sem máscara)")
            elif test_user.get('phone') == '(11) 98765-4321':
                print("❌ Telefone salvo com máscara (problema)")
            else:
                print(f"❌ Telefone inesperado: {test_user.get('phone')}")
        else:
            print("❌ Usuário não encontrado no banco de dados")
        
        print("\n🎉 Teste concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_phone_and_database()
