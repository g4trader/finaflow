#!/usr/bin/env python3
"""
Teste para verificar se o frontend está enviando o telefone corretamente
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_frontend_phone():
    """Testa se o frontend está enviando o telefone corretamente"""
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🧪 Testando frontend - envio do telefone...")
        
        # 1. Login
        print("1. Fazendo login...")
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
        
        # 2. Navegar para usuários
        print("2. Navegando para página de usuários...")
        driver.get("https://finaflow.vercel.app/users")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Página de usuários carregada")
        
        # 3. Abrir modal
        print("3. Abrindo modal...")
        novo_usuario_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Novo Usuário')]")
        novo_usuario_btn.click()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Modal aberto")
        
        # 4. Preencher formulário
        print("4. Preenchendo formulário...")
        
        # Nome
        nome_field = driver.find_element(By.XPATH, "//input[@placeholder='Digite o nome']")
        nome_field.send_keys("Teste Frontend Telefone")
        
        # Email
        email_field = driver.find_element(By.XPATH, "//input[@placeholder='email@exemplo.com']")
        email_field.send_keys("teste.frontend@exemplo.com")
        
        # Telefone - digitar número sem formatação
        telefone_field = driver.find_element(By.XPATH, "//input[@placeholder='(11) 99999-9999']")
        telefone_field.clear()
        telefone_field.send_keys("11987654321")  # Número diferente para teste
        time.sleep(1)
        
        valor_telefone_campo = telefone_field.get_attribute("value")
        print(f"   Valor do telefone no campo: '{valor_telefone_campo}'")
        
        # 5. Clicar no botão de criar
        print("5. Criando usuário...")
        criar_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Criar')]")
        criar_btn.click()
        
        # Aguardar modal fechar
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//h3[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Usuário criado")
        
        # 6. Verificar se usuário aparece na lista
        print("6. Verificando se usuário aparece na lista...")
        time.sleep(2)
        
        try:
            usuario_criado = driver.find_element(By.XPATH, "//td[contains(text(), 'Teste Frontend Telefone')]")
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
        
        # 7. Verificar logs do console
        print("7. Verificando logs do console...")
        logs = driver.get_log('browser')
        
        # Procurar por logs de debug
        debug_logs = [log for log in logs if 'formData antes de enviar' in log['message'] or 'Telefone sem máscara' in log['message'] or 'dataToSend' in log['message']]
        
        if debug_logs:
            print("✅ Logs de debug encontrados:")
            for log in debug_logs:
                print(f"   - {log['message']}")
        else:
            print("❌ Nenhum log de debug encontrado")
        
        print("\n🎉 Teste concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_frontend_phone()
