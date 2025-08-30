#!/usr/bin/env python3
"""
Teste de usabilidade para verificar as correções no CRUD de usuários
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_usability_fixes():
    """Testa as correções de usabilidade implementadas"""
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🧪 Iniciando testes de usabilidade...")
        
        # 1. Testar login
        print("1. Testando login...")
        driver.get("https://finaflow.vercel.app/login")
        
        # Aguardar carregamento da página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        # Preencher login
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin@finaflow.com")
        password_field.send_keys("admin123")
        
        # Fazer login
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
        login_button.click()
        
        # Aguardar redirecionamento para dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        print("✅ Login realizado com sucesso")
        
        # 2. Navegar para página de usuários
        print("2. Navegando para página de usuários...")
        driver.get("https://finaflow.vercel.app/users")
        
        # Aguardar carregamento da página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Página de usuários carregada")
        
        # 3. Testar modal de criação
        print("3. Testando modal de criação...")
        novo_usuario_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Novo Usuário')]")
        novo_usuario_btn.click()
        
        # Aguardar modal abrir
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Modal aberto com sucesso")
        
        # 4. Testar campo nome (verificar se não perde focus)
        print("4. Testando campo nome...")
        nome_field = driver.find_element(By.XPATH, "//input[@placeholder='Digite o nome']")
        nome_field.click()
        nome_field.send_keys("Teste")
        
        # Verificar se o valor foi digitado corretamente
        if nome_field.get_attribute("value") == "Teste":
            print("✅ Campo nome funcionando corretamente (sem perda de focus)")
        else:
            print("❌ Problema no campo nome")
        
        # 5. Testar campo telefone com máscara
        print("5. Testando campo telefone...")
        telefone_field = driver.find_element(By.XPATH, "//input[@placeholder='(11) 99999-9999']")
        telefone_field.click()
        telefone_field.clear()
        telefone_field.send_keys("11999999999")
        
        # Aguardar um pouco para a máscara ser aplicada
        time.sleep(1)
        
        valor_telefone = telefone_field.get_attribute("value")
        print(f"   Valor do telefone: {valor_telefone}")
        
        if "(11) 99999-9999" in valor_telefone:
            print("✅ Máscara de telefone aplicada corretamente")
        else:
            print("❌ Problema na máscara de telefone")
        
        # 6. Testar outros campos
        print("6. Testando outros campos...")
        email_field = driver.find_element(By.XPATH, "//input[@placeholder='email@exemplo.com']")
        email_field.send_keys("teste@exemplo.com")
        
        if email_field.get_attribute("value") == "teste@exemplo.com":
            print("✅ Campo email funcionando corretamente")
        else:
            print("❌ Problema no campo email")
        
        # 7. Testar criação de usuário
        print("7. Testando criação de usuário...")
        criar_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Criar Usuário')]")
        criar_btn.click()
        
        # Aguardar modal fechar
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//h2[contains(text(), 'Novo Usuário')]"))
        )
        
        print("✅ Usuário criado com sucesso")
        
        # 8. Verificar se o usuário aparece na lista
        print("8. Verificando se usuário aparece na lista...")
        time.sleep(2)  # Aguardar atualização da lista
        
        # Procurar pelo usuário criado
        try:
            usuario_criado = driver.find_element(By.XPATH, "//td[contains(text(), 'Teste')]")
            print("✅ Usuário encontrado na lista")
        except:
            print("❌ Usuário não encontrado na lista")
        
        print("\n🎉 Todos os testes de usabilidade concluídos!")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_usability_fixes()
