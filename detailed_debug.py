#!/usr/bin/env python3
"""
DEBUG DETALHADO - FinaFlow
Identificar problemas específicos na interface
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def detailed_debug():
    """Debug detalhado do frontend"""
    print("🔍 INICIANDO DEBUG DETALHADO DO FRONTEND")
    print("=" * 60)
    
    # Configurar Chrome sem headless para ver o que está acontecendo
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comentado para ver o que está acontecendo
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)
    
    try:
        # 1. Acessar página de login
        print("1️⃣ Acessando página de login...")
        driver.get("https://finaflow.vercel.app")
        
        # Aguardar carregamento
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Verificar título
        title = driver.title
        print(f"   📄 Título da página: '{title}'")
        
        # Verificar URL
        current_url = driver.current_url
        print(f"   🔗 URL atual: '{current_url}'")
        
        # 2. Verificar se a página carregou completamente
        print("\n2️⃣ Verificando carregamento da página...")
        
        # Aguardar um pouco mais
        time.sleep(5)
        
        # Verificar se há elementos básicos
        body = driver.find_element(By.TAG_NAME, "body")
        body_text = body.text[:200]  # Primeiros 200 caracteres
        print(f"   📝 Texto do body: '{body_text}...'")
        
        # 3. Verificar se há JavaScript errors
        print("\n3️⃣ Verificando erros JavaScript...")
        
        # Verificar console logs
        logs = driver.get_log('browser')
        if logs:
            print("   ⚠️ Logs do console:")
            for log in logs[:5]:  # Primeiros 5 logs
                print(f"      {log['level']}: {log['message']}")
        else:
            print("   ✅ Nenhum log de console encontrado")
        
        # 4. Verificar todos os elementos na página
        print("\n4️⃣ Verificando todos os elementos...")
        
        # Contar elementos
        all_elements = driver.find_elements(By.XPATH, "//*")
        print(f"   📊 Total de elementos na página: {len(all_elements)}")
        
        # Verificar tipos de elementos
        element_types = {}
        for element in all_elements:
            tag_name = element.tag_name
            element_types[tag_name] = element_types.get(tag_name, 0) + 1
        
        print("   📋 Tipos de elementos encontrados:")
        for tag, count in sorted(element_types.items()):
            print(f"      {tag}: {count}")
        
        # 5. Verificar especificamente por inputs
        print("\n5️⃣ Verificando inputs especificamente...")
        
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"   📝 Inputs encontrados: {len(inputs)}")
        
        for i, inp in enumerate(inputs):
            name = inp.get_attribute("name") or "sem name"
            type_attr = inp.get_attribute("type") or "sem type"
            placeholder = inp.get_attribute("placeholder") or "sem placeholder"
            id_attr = inp.get_attribute("id") or "sem id"
            class_attr = inp.get_attribute("class") or "sem class"
            print(f"      {i+1}. name='{name}', type='{type_attr}', placeholder='{placeholder}', id='{id_attr}', class='{class_attr}'")
        
        # 6. Verificar se há algum problema de renderização
        print("\n6️⃣ Verificando renderização...")
        
        # Verificar se há elementos com display: none
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, "[style*='display: none']")
        print(f"   👻 Elementos ocultos: {len(hidden_elements)}")
        
        # Verificar se há elementos com visibility: hidden
        invisible_elements = driver.find_elements(By.CSS_SELECTOR, "[style*='visibility: hidden']")
        print(f"   👻 Elementos invisíveis: {len(invisible_elements)}")
        
        # 7. Verificar se há iframes
        print("\n7️⃣ Verificando iframes...")
        
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"   🖼️ Iframes encontrados: {len(iframes)}")
        
        for i, iframe in enumerate(iframes):
            src = iframe.get_attribute("src") or "sem src"
            print(f"      {i+1}. src='{src}'")
        
        # 8. Verificar se há problemas de CSS
        print("\n8️⃣ Verificando CSS...")
        
        # Verificar se há estilos carregados
        style_elements = driver.find_elements(By.TAG_NAME, "style")
        print(f"   🎨 Elementos style: {len(style_elements)}")
        
        link_elements = driver.find_elements(By.TAG_NAME, "link")
        css_links = [link for link in link_elements if link.get_attribute("rel") == "stylesheet"]
        print(f"   🔗 Links CSS: {len(css_links)}")
        
        # 9. Tentar encontrar o formulário de outra forma
        print("\n9️⃣ Procurando formulário de forma alternativa...")
        
        # Procurar por texto que indica login
        login_texts = ["Entrar", "Login", "Sign in", "Username", "Email", "Senha", "Password"]
        for text in login_texts:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                if elements:
                    print(f"   ✅ Texto '{text}' encontrado em {len(elements)} elementos")
                    for elem in elements[:2]:  # Mostrar apenas os 2 primeiros
                        tag = elem.tag_name
                        text_content = elem.text[:50]  # Primeiros 50 caracteres
                        print(f"      - {tag}: '{text_content}...'")
            except:
                continue
        
        # 10. Verificar se há problemas de carregamento assíncrono
        print("\n🔟 Verificando carregamento assíncrono...")
        
        # Aguardar mais tempo para ver se elementos aparecem
        print("   ⏳ Aguardando 10 segundos para carregamento assíncrono...")
        time.sleep(10)
        
        # Verificar novamente por inputs
        inputs_after_wait = driver.find_elements(By.TAG_NAME, "input")
        print(f"   📝 Inputs após espera: {len(inputs_after_wait)}")
        
        if len(inputs_after_wait) > len(inputs):
            print("   ✅ Novos inputs apareceram após espera!")
            for i, inp in enumerate(inputs_after_wait):
                name = inp.get_attribute("name") or "sem name"
                type_attr = inp.get_attribute("type") or "sem type"
                placeholder = inp.get_attribute("placeholder") or "sem placeholder"
                print(f"      {i+1}. name='{name}', type='{type_attr}', placeholder='{placeholder}'")
        
        # 11. Verificar se há problemas de roteamento
        print("\n1️⃣1️⃣ Verificando roteamento...")
        
        # Verificar se há elementos de roteamento
        router_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='router'], [class*='router'], [id*='router']")
        print(f"   🛣️ Elementos de roteamento: {len(router_elements)}")
        
        # Verificar se há elementos de loading
        loading_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='loading'], [class*='spinner'], [class*='skeleton']")
        print(f"   ⏳ Elementos de loading: {len(loading_elements)}")
        
        # 12. Verificar se há problemas de autenticação
        print("\n1️⃣2️⃣ Verificando autenticação...")
        
        # Verificar se há tokens ou dados de auth
        auth_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='auth'], [id*='auth'], [data-testid*='auth']")
        print(f"   🔐 Elementos de autenticação: {len(auth_elements)}")
        
        # Verificar localStorage
        try:
            local_storage = driver.execute_script("return Object.keys(localStorage);")
            print(f"   💾 Chaves no localStorage: {local_storage}")
        except:
            print("   ❌ Não foi possível acessar localStorage")
        
        # 13. Verificar se há problemas de CORS ou rede
        print("\n1️⃣3️⃣ Verificando problemas de rede...")
        
        # Verificar se há erros de rede
        network_logs = driver.get_log('performance')
        if network_logs:
            print(f"   🌐 Logs de performance: {len(network_logs)}")
            for log in network_logs[:3]:  # Primeiros 3 logs
                print(f"      {log}")
        else:
            print("   ✅ Nenhum log de performance encontrado")
        
        # 14. Verificar se há problemas de JavaScript
        print("\n1️⃣4️⃣ Verificando JavaScript...")
        
        # Tentar executar JavaScript
        try:
            js_result = driver.execute_script("return document.readyState;")
            print(f"   📜 Document readyState: {js_result}")
        except Exception as e:
            print(f"   ❌ Erro ao executar JavaScript: {e}")
        
        # Verificar se há React ou outros frameworks
        try:
            react_elements = driver.execute_script("return window.React !== undefined;")
            print(f"   ⚛️ React detectado: {react_elements}")
        except:
            print("   ❌ Não foi possível verificar React")
        
        # 15. Verificar se há problemas de build
        print("\n1️⃣5️⃣ Verificando build...")
        
        # Verificar se há arquivos JS carregados
        script_elements = driver.find_elements(By.TAG_NAME, "script")
        print(f"   📜 Scripts carregados: {len(script_elements)}")
        
        for i, script in enumerate(script_elements[:5]):  # Primeiros 5 scripts
            src = script.get_attribute("src") or "inline"
            print(f"      {i+1}. {src}")
        
    except Exception as e:
        print(f"❌ Erro durante debug detalhado: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n" + "=" * 60)
        print("🏁 DEBUG DETALHADO CONCLUÍDO")
        print("Pressione Enter para fechar o navegador...")
        input()
        driver.quit()

if __name__ == "__main__":
    detailed_debug()
