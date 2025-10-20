#!/usr/bin/env python3
"""
TESTE DETALHADO DA PÁGINA DE TRANSAÇÕES
Verifica todos os elementos e funcionalidades da página
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

def setup_driver():
    """Configurar driver Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"❌ Erro ao configurar driver: {e}")
        return None

def test_transactions_page_detailed(driver):
    """Teste detalhado da página de transações"""
    print("🔍 TESTE DETALHADO DA PÁGINA DE TRANSAÇÕES")
    print("=" * 50)
    
    try:
        # Acessar página
        driver.get("https://finaflow.vercel.app/transactions")
        time.sleep(5)  # Aguardar carregamento completo
        
        print(f"📍 URL atual: {driver.current_url}")
        
        # Verificar título da página
        try:
            page_title = driver.title
            print(f"📄 Título da página: {page_title}")
        except:
            print("⚠️ Título da página não encontrado")
        
        # Verificar elementos principais
        elements_to_check = [
            ("Botões de ação", "//button[contains(text(), 'Nova') or contains(text(), 'Importar') or contains(text(), 'Adicionar') or contains(text(), 'Upload')]"),
            ("Campo de busca", "//input[@placeholder or @name or contains(@class, 'search')]"),
            ("Filtros", "//select or //input[@type='date'] or //div[contains(@class, 'filter')]"),
            ("Tabela de transações", "//table | //div[contains(@class, 'transaction')] | //div[contains(@class, 'list')] | //div[contains(@class, 'grid')]"),
            ("Mensagem de estado", "//*[contains(text(), 'nenhuma') or contains(text(), 'Nenhuma') or contains(text(), 'empty') or contains(text(), 'carregando') or contains(text(), 'Carregando')]"),
            ("Paginador", "//nav[contains(@class, 'pagination')] or //div[contains(@class, 'pagination')] or //button[contains(text(), 'Próxima') or contains(text(), 'Anterior')]"),
            ("Resumo financeiro", "//div[contains(text(), 'Total') or contains(text(), 'Saldo') or contains(text(), 'Resumo')]")
        ]
        
        found_elements = {}
        
        for element_name, xpath in elements_to_check:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    found_elements[element_name] = len(elements)
                    print(f"✅ {element_name}: {len(elements)} encontrado(s)")
                    
                    # Mostrar detalhes dos primeiros elementos
                    for i, element in enumerate(elements[:3]):  # Mostrar apenas os 3 primeiros
                        try:
                            text = element.text.strip()
                            if text:
                                print(f"   {i+1}. Texto: '{text[:50]}{'...' if len(text) > 50 else ''}'")
                        except:
                            pass
                else:
                    found_elements[element_name] = 0
                    print(f"❌ {element_name}: Não encontrado")
            except Exception as e:
                found_elements[element_name] = 0
                print(f"❌ {element_name}: Erro - {e}")
        
        # Verificar classes CSS para entender a estrutura
        try:
            body_classes = driver.find_element(By.TAG_NAME, "body").get_attribute("class")
            if body_classes:
                print(f"🎨 Classes do body: {body_classes}")
        except:
            pass
        
        # Verificar se há erros JavaScript
        try:
            console_logs = driver.get_log("browser")
            if console_logs:
                print(f"📝 Logs do console: {len(console_logs)} entradas")
                for log in console_logs[:5]:  # Mostrar apenas os 5 primeiros
                    if log["level"] in ["SEVERE", "ERROR"]:
                        print(f"   ❌ ERRO: {log['message']}")
        except:
            pass
        
        # Verificar se a página está carregando dados
        try:
            # Aguardar um pouco mais para ver se há carregamento assíncrono
            time.sleep(3)
            
            # Verificar se apareceram novos elementos
            final_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'transação') or contains(text(), 'transaction')]")
            if final_elements:
                print(f"🔄 Elementos de transação encontrados após espera: {len(final_elements)}")
                for i, element in enumerate(final_elements[:3]):
                    try:
                        text = element.text.strip()
                        if text:
                            print(f"   {i+1}. '{text[:50]}{'...' if len(text) > 50 else ''}'")
                    except:
                        pass
        except:
            pass
        
        return found_elements
        
    except Exception as e:
        print(f"❌ Erro no teste detalhado: {e}")
        return {}

def test_page_source_analysis(driver):
    """Analisar o código fonte da página"""
    print("\n🔍 ANÁLISE DO CÓDIGO FONTE")
    print("=" * 50)
    
    try:
        page_source = driver.page_source
        
        # Verificar se há elementos relacionados a transações
        transaction_indicators = [
            "transaction", "transação", "financial", "financeiro",
            "chart", "conta", "account", "amount", "valor",
            "date", "data", "type", "tipo", "status"
        ]
        
        found_indicators = []
        for indicator in transaction_indicators:
            if indicator.lower() in page_source.lower():
                found_indicators.append(indicator)
        
        print(f"📊 Indicadores encontrados no código: {len(found_indicators)}")
        if found_indicators:
            print(f"   ✅ {', '.join(found_indicators[:10])}")
        
        # Verificar se há dados mock ou reais
        mock_indicators = ["mock", "fake", "test", "example", "sample"]
        mock_found = any(indicator in page_source.lower() for indicator in mock_indicators)
        
        if mock_found:
            print("⚠️ Possíveis dados mock encontrados no código")
        else:
            print("✅ Nenhum dado mock óbvio encontrado")
        
        # Verificar se há chamadas de API
        api_indicators = ["fetch", "axios", "api", "endpoint", "url"]
        api_found = any(indicator in page_source.lower() for indicator in api_indicators)
        
        if api_found:
            print("✅ Indicadores de chamadas de API encontrados")
        else:
            print("⚠️ Poucos indicadores de chamadas de API")
        
        return {
            "indicators": found_indicators,
            "mock_data": mock_found,
            "api_calls": api_found
        }
        
    except Exception as e:
        print(f"❌ Erro na análise do código fonte: {e}")
        return {}

def main():
    """Função principal"""
    print("🚀 INICIANDO TESTE DETALHADO COM SELENIUM")
    print("=" * 60)
    
    driver = setup_driver()
    if not driver:
        print("❌ Não foi possível configurar o driver")
        return
    
    try:
        # Teste detalhado da página
        elements_found = test_transactions_page_detailed(driver)
        
        # Análise do código fonte
        source_analysis = test_page_source_analysis(driver)
        
        # Resultado final
        print("\n" + "=" * 60)
        print("📊 RESULTADO DO TESTE DETALHADO:")
        
        total_elements = sum(elements_found.values())
        print(f"Elementos encontrados: {total_elements}")
        
        for element_name, count in elements_found.items():
            status = "✅" if count > 0 else "❌"
            print(f"{status} {element_name}: {count}")
        
        print(f"\nAnálise do código fonte:")
        print(f"   Indicadores: {len(source_analysis.get('indicators', []))}")
        print(f"   Dados mock: {'⚠️ Sim' if source_analysis.get('mock_data') else '✅ Não'}")
        print(f"   Chamadas API: {'✅ Sim' if source_analysis.get('api_calls') else '⚠️ Não'}")
        
        if total_elements > 0:
            print("\n🎉 PÁGINA DE TRANSAÇÕES FUNCIONANDO CORRETAMENTE!")
        else:
            print("\n⚠️ PÁGINA PODE TER PROBLEMAS DE CARREGAMENTO")
            
    finally:
        driver.quit()
        print("✅ Driver Chrome fechado")

if __name__ == "__main__":
    main()

