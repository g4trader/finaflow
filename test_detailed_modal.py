#!/usr/bin/env python3
"""
Teste detalhado para verificar problemas na modal de usuários
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_detailed_modal():
    """Teste detalhado da modal de usuários"""
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🧪 Teste detalhado da modal de usuários...")
        
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
        
        # 4. Verificar se há erros na página
        print("4. Verificando erros na página...")
        page_source = driver.page_source.lower()
        
        if "error" in page_source:
            print("❌ Página contém texto de erro")
        else:
            print("✅ Nenhum erro encontrado na página")
        
        if "404" in page_source:
            print("❌ Página contém erro 404")
        else:
            print("✅ Nenhum erro 404 encontrado")
        
        # 5. Listar todos os botões na modal
        print("5. Listando botões na modal...")
        try:
            modal = driver.find_element(By.XPATH, "//h3[contains(text(), 'Novo Usuário')]/ancestor::div[contains(@class, 'fixed')]")
            buttons = modal.find_elements(By.TAG_NAME, "button")
            print(f"   Botões encontrados na modal: {len(buttons)}")
            
            for i, btn in enumerate(buttons):
                try:
                    text = btn.text.strip()
                    print(f"   Botão {i+1}: '{text}'")
                except:
                    print(f"   Botão {i+1}: [sem texto]")
                    
        except Exception as e:
            print(f"   Erro ao listar botões: {e}")
        
        # 6. Testar campo nome
        print("6. Testando campo nome...")
        try:
            nome_field = driver.find_element(By.XPATH, "//input[@placeholder='Digite o nome']")
            nome_field.click()
            nome_field.clear()
            nome_field.send_keys("Teste")
            
            valor_nome = nome_field.get_attribute("value")
            print(f"   Valor do nome: '{valor_nome}'")
            
            if valor_nome == "Teste":
                print("✅ Campo nome funcionando corretamente")
            else:
                print(f"❌ Problema no campo nome. Esperado: 'Teste', Obtido: '{valor_nome}'")
                
        except Exception as e:
            print(f"❌ Erro no campo nome: {e}")
        
        # 7. Testar campo telefone
        print("7. Testando campo telefone...")
        try:
            telefone_field = driver.find_element(By.XPATH, "//input[@placeholder='(11) 99999-9999']")
            telefone_field.click()
            telefone_field.clear()
            telefone_field.send_keys("11999999999")
            time.sleep(1)
            
            valor_telefone = telefone_field.get_attribute("value")
            print(f"   Valor do telefone: '{valor_telefone}'")
            
            if "(11) 99999-9999" in valor_telefone:
                print("✅ Máscara de telefone aplicada corretamente")
            else:
                print(f"❌ Problema na máscara de telefone. Esperado: '(11) 99999-9999', Obtido: '{valor_telefone}'")
                
        except Exception as e:
            print(f"❌ Erro no campo telefone: {e}")
        
        # 8. Tentar encontrar botão de submit
        print("8. Procurando botão de submit...")
        submit_selectors = [
            "//button[contains(text(), 'Criar Usuário')]",
            "//button[contains(text(), 'Criar')]",
            "//button[contains(text(), 'Salvar')]",
            "//button[contains(text(), 'Submit')]",
            "//button[@type='submit']",
            "//button[contains(@class, 'primary')]"
        ]
        
        submit_button = None
        for selector in submit_selectors:
            try:
                submit_button = driver.find_element(By.XPATH, selector)
                print(f"✅ Botão encontrado com selector: {selector}")
                print(f"   Texto do botão: '{submit_button.text}'")
                break
            except:
                continue
        
        if submit_button:
            print("✅ Botão de submit encontrado")
        else:
            print("❌ Nenhum botão de submit encontrado")
        
        # 9. Verificar se há problemas de rede
        print("9. Verificando problemas de rede...")
        logs = driver.get_log('browser')
        network_errors = [log for log in logs if '404' in log['message'] or 'error' in log['message'].lower()]
        
        if network_errors:
            print("❌ Encontrados erros de rede:")
            for error in network_errors[:3]:  # Mostrar apenas os primeiros 3
                print(f"   - {error['message']}")
        else:
            print("✅ Nenhum erro de rede encontrado")
        
        print("\n🎉 Teste detalhado concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_detailed_modal()
