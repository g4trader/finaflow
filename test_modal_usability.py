#!/usr/bin/env python3
"""
Teste específico para problemas de usabilidade na modal de usuários
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def test_modal_usability():
    """Testa especificamente os problemas de usabilidade na modal"""
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🧪 Testando usabilidade da modal de usuários...")
        
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
        print("3. Abrindo modal de novo usuário...")
        novo_usuario_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Novo Usuário')]")
        novo_usuario_btn.click()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Modal aberto")
        
        # 4. Testar campo nome - verificar se perde focus
        print("4. Testando campo nome...")
        nome_field = driver.find_element(By.XPATH, "//input[@placeholder='Digite o nome']")
        nome_field.click()
        nome_field.clear()
        
        # Digitar caractere por caractere para testar focus
        nome_field.send_keys("T")
        time.sleep(0.5)
        nome_field.send_keys("e")
        time.sleep(0.5)
        nome_field.send_keys("s")
        time.sleep(0.5)
        nome_field.send_keys("t")
        time.sleep(0.5)
        nome_field.send_keys("e")
        
        valor_nome = nome_field.get_attribute("value")
        print(f"   Valor do nome: '{valor_nome}'")
        
        if valor_nome == "Teste":
            print("✅ Campo nome funcionando corretamente (sem perda de focus)")
        else:
            print(f"❌ Problema no campo nome. Esperado: 'Teste', Obtido: '{valor_nome}'")
        
        # 5. Testar campo telefone - verificar máscara
        print("5. Testando campo telefone...")
        telefone_field = driver.find_element(By.XPATH, "//input[@placeholder='(11) 99999-9999']")
        telefone_field.click()
        telefone_field.clear()
        
        # Digitar número sem formatação
        telefone_field.send_keys("11999999999")
        time.sleep(1)
        
        valor_telefone = telefone_field.get_attribute("value")
        print(f"   Valor do telefone: '{valor_telefone}'")
        
        if "(11) 99999-9999" in valor_telefone:
            print("✅ Máscara de telefone aplicada corretamente")
        else:
            print(f"❌ Problema na máscara de telefone. Esperado: '(11) 99999-9999', Obtido: '{valor_telefone}'")
        
        # 6. Testar campo email
        print("6. Testando campo email...")
        email_field = driver.find_element(By.XPATH, "//input[@placeholder='email@exemplo.com']")
        email_field.click()
        email_field.clear()
        email_field.send_keys("teste@exemplo.com")
        
        valor_email = email_field.get_attribute("value")
        print(f"   Valor do email: '{valor_email}'")
        
        if valor_email == "teste@exemplo.com":
            print("✅ Campo email funcionando corretamente")
        else:
            print(f"❌ Problema no campo email. Esperado: 'teste@exemplo.com', Obtido: '{valor_email}'")
        
        # 7. Testar criação para verificar se telefone é salvo corretamente
        print("7. Testando criação de usuário...")
        criar_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Criar Usuário')]")
        criar_btn.click()
        
        # Aguardar modal fechar
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//h3[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Usuário criado")
        
        # 8. Verificar se o usuário aparece na lista
        print("8. Verificando se usuário aparece na lista...")
        time.sleep(2)
        
        try:
            # Procurar pelo usuário criado
            usuario_criado = driver.find_element(By.XPATH, "//td[contains(text(), 'Teste')]")
            print("✅ Usuário encontrado na lista")
            
            # Verificar se o telefone está formatado corretamente na lista
            try:
                telefone_na_lista = driver.find_element(By.XPATH, "//td[contains(text(), '(11) 99999-9999')]")
                print("✅ Telefone formatado corretamente na lista")
            except:
                print("❌ Telefone não encontrado ou não formatado corretamente na lista")
                
        except:
            print("❌ Usuário não encontrado na lista")
        
        print("\n🎉 Teste de usabilidade da modal concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_modal_usability()
