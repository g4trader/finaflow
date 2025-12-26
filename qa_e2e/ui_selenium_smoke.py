#!/usr/bin/env python3
"""
Testes E2E UI com Selenium
Valida páginas críticas e consistência de valores
"""

import sys
import os
import json
import time
import re
from pathlib import Path
from decimal import Decimal
from typing import Dict, Optional

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    import requests
except ImportError as e:
    print(f"❌ Erro: dependência não instalada: {e}")
    print("Execute: pip install selenium webdriver-manager requests")
    sys.exit(1)

OUT_DIR = Path(__file__).parent / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR = OUT_DIR / "screenshots"
HTML_DIR = OUT_DIR / "html"
SCREENSHOTS_DIR.mkdir(exist_ok=True)
HTML_DIR.mkdir(exist_ok=True)

def parse_brl_currency(text: str) -> Decimal:
    """Converte R$ 1.098.490,83 para Decimal"""
    if not text:
        return Decimal(0)
    # Remover R$, espaços e pontos de milhar
    cleaned = text.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except:
        return Decimal(0)

def login_api(backend_url: str, email: str, password: str) -> str:
    """Faz login e retorna token"""
    response = requests.post(
        f"{backend_url}/api/v1/auth/login",
        json={"username": email, "password": password}
    )
    if response.status_code != 200:
        raise Exception(f"Login falhou: {response.status_code}")
    return response.json().get("access_token")

def fetch_annual_summary(backend_url: str, token: str, year: int) -> Dict:
    """Busca resumo anual da API"""
    response = requests.get(
        f"{backend_url}/api/v1/financial/annual-summary?year={year}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        raise Exception(f"API falhou: {response.status_code}")
    return response.json()

def setup_driver(headless: bool = True):
    """Configura driver Selenium"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def take_screenshot(driver, name: str, success: bool = True):
    """Tira screenshot"""
    suffix = "PASS" if success else "FAIL"
    path = SCREENSHOTS_DIR / f"{name}_{suffix}.png"
    driver.save_screenshot(str(path))
    return path

def save_page_html(driver, name: str):
    """Salva HTML da página"""
    path = HTML_DIR / f"{name}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    return path

def test_dashboard(driver, frontend_url: str, year: int, backend_url: str, token: str) -> Dict:
    """Testa página /dashboard"""
    print(f"\n📊 Testando /dashboard?year={year}")
    
    url = f"{frontend_url}/dashboard?year={year}"
    driver.get(url)
    
    # Aguardar carregamento
    print("   ⏳ Aguardando carregamento...")
    time.sleep(8)
    
    # Verificar se há erro de rede
    page_text = driver.page_source.lower()
    page_title = driver.title
    current_url = driver.current_url
    
    print(f"   📄 Título: {page_title}")
    print(f"   🔗 URL atual: {current_url}")
    
    if "network error" in page_text or "failed to fetch" in page_text:
        print("   ❌ Network error detectado")
        take_screenshot(driver, "dashboard", False)
        save_page_html(driver, "dashboard")
        return {"status": "FAIL", "error": "Network error detectado", "url": current_url}
    
    # Procurar por cards de totais - melhorar seletores
    totals = {}
    try:
        wait = WebDriverWait(driver, 15)
        
        # Tentar encontrar cards por diferentes estratégias
        # Estratégia 1: Procurar por elementos com classes comuns de cards
        card_selectors = [
            "//div[contains(@class, 'card')]",
            "//div[contains(@class, 'Card')]",
            "//div[contains(@class, 'bg-')]",
            "//*[contains(text(), 'Receita Total')]",
            "//*[contains(text(), 'Despesas Totais')]",
            "//*[contains(text(), 'Custos Totais')]"
        ]
        
        found_elements = []
        for selector in card_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    found_elements.extend(elements)
                    print(f"   ✅ Encontrados {len(elements)} elementos com selector: {selector[:50]}")
            except:
                pass
        
        # Procurar por textos específicos e extrair valores próximos
        text_patterns = {
            "revenue": ["receita", "receitas", "revenue"],
            "expense": ["despesa", "despesas", "expense"],
            "cost": ["custo", "custos", "cost"]
        }
        
        for field, patterns in text_patterns.items():
            for pattern in patterns:
                try:
                    # Procurar elemento com o texto
                    xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]"
                    elements = driver.find_elements(By.XPATH, xpath)
                    
                    for elem in elements[:3]:  # Limitar a 3 elementos
                        try:
                            # Tentar encontrar valor no mesmo elemento ou próximo
                            text = elem.text
                            if pattern in text.lower():
                                # Procurar número no texto do elemento ou próximo
                                parent = elem.find_element(By.XPATH, "./..")
                                all_text = parent.text
                                
                                # Extrair valores monetários do texto
                                import re
                                money_pattern = r'R\$\s*([\d.,]+)'
                                matches = re.findall(money_pattern, all_text)
                                
                                if matches:
                                    value_str = matches[0]
                                    value = parse_brl_currency(f"R$ {value_str}")
                                    if value > 0:
                                        totals[field] = value
                                        print(f"   ✅ {field}: R$ {value}")
                                        break
                        except Exception as e:
                            continue
                    
                    if field in totals:
                        break
                except:
                    continue
        
        # Se não encontrou, tentar buscar todos os números na página
        if not totals:
            print("   ⚠️  Não encontrou valores específicos, tentando busca geral...")
            page_text_full = driver.page_source
            # Buscar padrões de valores monetários
            import re
            money_matches = re.findall(r'R\$\s*([\d.,]+)', page_text_full)
            if money_matches:
                print(f"   📊 Encontrados {len(money_matches)} valores monetários na página")
                
    except Exception as e:
        print(f"   ⚠️  Erro ao extrair valores: {e}")
        import traceback
        traceback.print_exc()
    
    # Comparar com API
    try:
        api_data = fetch_annual_summary(backend_url, token, year)
        api_totals = api_data.get("totals", {})
        
        mismatches = []
        tolerance = Decimal("0.01")
        
        for field in ["revenue", "expense", "cost"]:
            ui_val = totals.get(field, Decimal(0))
            api_val = Decimal(str(api_totals.get(field, 0)))
            diff = abs(ui_val - api_val)
            
            if ui_val > 0 or api_val > 0:  # Só comparar se houver valor
                if diff > tolerance:
                    mismatches.append({
                        "field": field,
                        "ui": float(ui_val),
                        "api": float(api_val),
                        "diff": float(diff)
                    })
                    print(f"   ⚠️  Mismatch {field}: UI={ui_val}, API={api_val}, Diff={diff}")
                else:
                    print(f"   ✅ {field} OK: UI={ui_val}, API={api_val}")
        
        # Se não encontrou valores na UI mas API tem, considerar como parcial
        if not totals and api_totals:
            print("   ⚠️  Não foi possível extrair valores da UI, mas API retornou dados")
            status = "PARTIAL"
        elif len(mismatches) == 0:
            status = "PASS"
        else:
            status = "FAIL"
            
    except Exception as e:
        print(f"   ❌ Erro ao comparar com API: {e}")
        status = "ERROR"
        api_totals = {}
        mismatches = []
    
    take_screenshot(driver, "dashboard", status == "PASS")
    save_page_html(driver, "dashboard")
    
    return {
        "status": status,
        "totals": {k: float(v) for k, v in totals.items()},
        "api_totals": api_totals,
        "mismatches": mismatches,
        "url": current_url,
        "title": page_title
    }

def test_dashboard_operational(driver, frontend_url: str) -> Dict:
    """Testa página /dashboard-operational"""
    print(f"\n📊 Testando /dashboard-operational")
    
    url = f"{frontend_url}/dashboard-operational"
    driver.get(url)
    
    print("   ⏳ Aguardando carregamento...")
    time.sleep(8)
    
    # Verificar componentes
    components_found = {}
    page_text = driver.page_source.lower()
    page_title = driver.title
    current_url = driver.current_url
    
    print(f"   📄 Título: {page_title}")
    print(f"   🔗 URL atual: {current_url}")
    
    components = {
        "disponibilidades": ["disponibilidade", "bancos", "caixa", "investimento", "total disponível"],
        "alertas": ["alerta", "vencida", "vencido", "tudo em dia"],
        "previsto_vs_realizado": ["previsto", "realizado", "forecast", "gráfico"],
        "contas_pagar": ["pagar", "payable", "contas a pagar"],
        "contas_receber": ["receber", "receivable", "contas a receber"]
    }
    
    for comp_name, keywords in components.items():
        found = any(kw in page_text for kw in keywords)
        components_found[comp_name] = found
        status_icon = "✅" if found else "❌"
        print(f"   {status_icon} {comp_name}: {'Encontrado' if found else 'Não encontrado'}")
    
    all_found = all(components_found.values())
    
    # Verificar erros
    has_error = "network error" in page_text or "failed to fetch" in page_text or "404" in page_text or "not found" in page_text
    
    if has_error:
        print("   ❌ Erro detectado na página")
    
    # Tentar encontrar elementos visuais específicos
    try:
        # Procurar por cards ou seções
        cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'card') or contains(@class, 'Card')]")
        print(f"   📦 Encontrados {len(cards)} cards/seções na página")
    except:
        pass
    
    status = "PASS" if all_found and not has_error else "FAIL"
    take_screenshot(driver, "dashboard_operational", status == "PASS")
    save_page_html(driver, "dashboard_operational")
    
    return {
        "status": status,
        "components": components_found,
        "has_error": has_error,
        "url": current_url,
        "title": page_title,
        "cards_found": len(cards) if 'cards' in locals() else 0
    }

def test_financial_forecasts(driver, frontend_url: str) -> Dict:
    """Testa página /financial-forecasts"""
    print(f"\n📊 Testando /financial-forecasts")
    
    url = f"{frontend_url}/financial-forecasts"
    driver.get(url)
    
    print("   ⏳ Aguardando carregamento...")
    time.sleep(8)
    
    # Verificar erros
    page_text = driver.page_source.lower()
    page_title = driver.title
    current_url = driver.current_url
    
    print(f"   📄 Título: {page_title}")
    print(f"   🔗 URL atual: {current_url}")
    
    # Tentar obter console logs
    console_logs = []
    try:
        if hasattr(driver, "get_log"):
            console_logs = driver.get_log("browser")
    except:
        pass
    
    has_cors_error = any("cors" in str(log).lower() for log in console_logs) or "cors" in page_text
    has_network_error = "network error" in page_text or "failed to fetch" in page_text or "fetch failed" in page_text
    has_500_error = "500" in page_text or "internal server error" in page_text or "error 500" in page_text
    
    has_error = has_cors_error or has_network_error or has_500_error
    
    # Verificar se a página carregou conteúdo
    has_content = len(page_text) > 1000  # Página tem conteúdo significativo
    has_table_or_list = "table" in page_text or "lista" in page_text or "previs" in page_text
    
    print(f"   📊 Tamanho da página: {len(page_text)} caracteres")
    print(f"   {'✅' if has_content else '❌'} Conteúdo: {'Sim' if has_content else 'Não'}")
    print(f"   {'✅' if has_table_or_list else '❌'} Tabela/Lista: {'Sim' if has_table_or_list else 'Não'}")
    print(f"   {'❌' if has_cors_error else '✅'} CORS: {'Erro detectado' if has_cors_error else 'OK'}")
    print(f"   {'❌' if has_network_error else '✅'} Network: {'Erro detectado' if has_network_error else 'OK'}")
    print(f"   {'❌' if has_500_error else '✅'} 500: {'Erro detectado' if has_500_error else 'OK'}")
    
    if console_logs:
        print(f"   📋 Console logs: {len(console_logs)} entradas")
        # Mostrar erros do console
        errors = [log for log in console_logs if log.get('level') == 'SEVERE']
        if errors:
            print(f"   ⚠️  {len(errors)} erros no console:")
            for err in errors[:3]:
                print(f"      - {err.get('message', '')[:100]}")
    
    status = "PASS" if not has_error and has_content else "FAIL"
    take_screenshot(driver, "financial_forecasts", status == "PASS")
    save_page_html(driver, "financial_forecasts")
    
    # Salvar console logs
    if console_logs:
        with open(OUT_DIR / "financial_forecasts_console.json", "w") as f:
            json.dump([{"level": log.get('level'), "message": log.get('message')} for log in console_logs], f, indent=2)
    
    return {
        "status": status,
        "has_cors_error": has_cors_error,
        "has_network_error": has_network_error,
        "has_500_error": has_500_error,
        "has_content": has_content,
        "has_table_or_list": has_table_or_list,
        "url": current_url,
        "title": page_title,
        "console_logs_count": len(console_logs),
        "console_errors": [{"level": log.get('level'), "message": log.get('message')} for log in console_logs if log.get('level') == 'SEVERE'][:5]
    }

def main():
    frontend_url = os.getenv("FRONTEND_URL", "https://finaflow-lcz5.vercel.app")
    backend_url = os.getenv("BACKEND_URL", "https://finaflow-backend-staging-642830139828.us-central1.run.app")
    email = os.getenv("QA_EMAIL", "qa@finaflow.test")
    password = os.getenv("QA_PASSWORD", "QaFinaflow123!")
    year = int(os.getenv("YEAR", "2025"))
    
    print("🚀 Iniciando testes UI com Selenium")
    print(f"   Frontend: {frontend_url}")
    print(f"   Backend: {backend_url}")
    
    # Obter token
    print("\n🔐 Fazendo login na API...")
    try:
        token = login_api(backend_url, email, password)
        print("✅ Login realizado")
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return 1
    
    # Setup driver
    print("\n🌐 Configurando Selenium...")
    driver = setup_driver(headless=True)
    
    results = {}
    
    try:
        # Login no frontend
        print("\n🔐 Fazendo login no frontend...")
        driver.get(f"{frontend_url}/login")
        time.sleep(2)
        
        # Preencher formulário
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys(email)
            password_input.send_keys(password)
            
            # Clicar em login
            login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar') or contains(text(), 'Login')]")
            login_button.click()
            
            # Aguardar redirecionamento
            time.sleep(5)
            
            print("✅ Login no frontend realizado")
        except Exception as e:
            print(f"⚠️  Erro no login frontend: {e}")
            take_screenshot(driver, "login", False)
        
        # Testar páginas
        results["dashboard"] = test_dashboard(driver, frontend_url, year, backend_url, token)
        results["dashboard_operational"] = test_dashboard_operational(driver, frontend_url)
        results["financial_forecasts"] = test_financial_forecasts(driver, frontend_url)
        
    finally:
        driver.quit()
    
    # Salvar resultados
    with open(OUT_DIR / "ui_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Resumo
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    all_pass = all(r.get("status") == "PASS" for r in results.values())
    
    for name, result in results.items():
        status = result.get("status", "UNKNOWN")
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} {name}: {status}")
    
    if all_pass:
        print("\n✅ Todos os testes UI passaram!")
        return 0
    else:
        print("\n❌ Alguns testes UI falharam")
        return 1

if __name__ == "__main__":
    sys.exit(main())

