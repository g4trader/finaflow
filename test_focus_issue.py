#!/usr/bin/env python3
"""
Teste específico para confirmar o problema de perda de focus
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_focus_issue():
    """Testa especificamente o problema de perda de focus"""
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🧪 Testando problema de perda de focus...")
        
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
        
        # 4. Testar campo nome com re-localização
        print("4. Testando campo nome com re-localização...")
        
        # Localizar o campo
        nome_field = driver.find_element(By.XPATH, "//input[@placeholder='Digite o nome']")
        nome_field.click()
        nome_field.clear()
        
        # Digitar caractere por caractere, re-localizando o elemento a cada vez
        for i, char in enumerate("Teste"):
            print(f"   Digitando caractere {i+1}: '{char}'")
            
            # Re-localizar o elemento a cada caractere
            nome_field = driver.find_element(By.XPATH, "//input[@placeholder='Digite o nome']")
            nome_field.send_keys(char)
            
            # Verificar se o valor foi mantido
            valor_atual = nome_field.get_attribute("value")
            print(f"   Valor atual: '{valor_atual}'")
            
            # Aguardar um pouco
            time.sleep(0.5)
        
        # Verificar valor final
        nome_field = driver.find_element(By.XPATH, "//input[@placeholder='Digite o nome']")
        valor_final = nome_field.get_attribute("value")
        print(f"   Valor final: '{valor_final}'")
        
        if valor_final == "Teste":
            print("✅ Campo nome funcionando corretamente")
        else:
            print(f"❌ Problema no campo nome. Esperado: 'Teste', Obtido: '{valor_final}'")
        
        # 5. Testar campo telefone
        print("5. Testando campo telefone...")
        telefone_field = driver.find_element(By.XPATH, "//input[@placeholder='(11) 99999-9999']")
        telefone_field.click()
        telefone_field.clear()
        
        # Digitar número
        telefone_field.send_keys("11999999999")
        time.sleep(1)
        
        # Re-localizar e verificar
        telefone_field = driver.find_element(By.XPATH, "//input[@placeholder='(11) 99999-9999']")
        valor_telefone = telefone_field.get_attribute("value")
        print(f"   Valor do telefone: '{valor_telefone}'")
        
        if "(11) 99999-9999" in valor_telefone:
            print("✅ Máscara de telefone aplicada corretamente")
        else:
            print(f"❌ Problema na máscara de telefone. Esperado: '(11) 99999-9999', Obtido: '{valor_telefone}'")
        
        print("\n🎉 Teste de focus concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_focus_issue()
