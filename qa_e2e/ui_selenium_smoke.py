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
    time.sleep(5)
    
    # Verificar se há erro de rede
    page_text = driver.page_source.lower()
    if "network error" in page_text or "failed to fetch" in page_text:
        take_screenshot(driver, "dashboard", False)
        save_page_html(driver, "dashboard")
        return {"status": "FAIL", "error": "Network error detectado"}
    
    # Procurar por cards de totais
    totals = {}
    try:
        # Tentar encontrar elementos com valores
        wait = WebDriverWait(driver, 10)
        
        # Procurar por textos que indicam os cards
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Receita') or contains(text(), 'Despesa') or contains(text(), 'Custo')]")
        
        for elem in elements:
            text = elem.text
            parent = elem.find_element(By.XPATH, "./..")
            value_elem = None
            try:
                # Tentar encontrar valor próximo
                value_elem = parent.find_element(By.XPATH, ".//*[contains(@class, 'text-')]")
            except:
                pass
            
            if value_elem:
                value_text = value_elem.text
                if "receita" in text.lower():
                    totals["revenue"] = parse_brl_currency(value_text)
                elif "despesa" in text.lower():
                    totals["expense"] = parse_brl_currency(value_text)
                elif "custo" in text.lower():
                    totals["cost"] = parse_brl_currency(value_text)
    except Exception as e:
        print(f"⚠️  Erro ao extrair valores: {e}")
    
    # Comparar com API
    api_data = fetch_annual_summary(backend_url, token, year)
    api_totals = api_data.get("totals", {})
    
    mismatches = []
    tolerance = Decimal("0.01")
    
    for field in ["revenue", "expense", "cost"]:
        ui_val = totals.get(field, Decimal(0))
        api_val = Decimal(str(api_totals.get(field, 0)))
        diff = abs(ui_val - api_val)
        
        if diff > tolerance:
            mismatches.append({
                "field": field,
                "ui": float(ui_val),
                "api": float(api_val),
                "diff": float(diff)
            })
    
    take_screenshot(driver, "dashboard", len(mismatches) == 0)
    save_page_html(driver, "dashboard")
    
    return {
        "status": "PASS" if len(mismatches) == 0 else "FAIL",
        "totals": {k: float(v) for k, v in totals.items()},
        "api_totals": api_totals,
        "mismatches": mismatches
    }

def test_dashboard_operational(driver, frontend_url: str) -> Dict:
    """Testa página /dashboard-operational"""
    print(f"\n📊 Testando /dashboard-operational")
    
    url = f"{frontend_url}/dashboard-operational"
    driver.get(url)
    
    time.sleep(5)
    
    # Verificar componentes
    components_found = {}
    page_text = driver.page_source.lower()
    
    components = {
        "disponibilidades": ["disponibilidade", "bancos", "caixa", "investimento"],
        "alertas": ["alerta", "vencida", "vencido"],
        "previsto_vs_realizado": ["previsto", "realizado", "forecast"],
        "contas_pagar": ["pagar", "payable"],
        "contas_receber": ["receber", "receivable"]
    }
    
    for comp_name, keywords in components.items():
        found = any(kw in page_text for kw in keywords)
        components_found[comp_name] = found
    
    all_found = all(components_found.values())
    
    # Verificar erros
    has_error = "network error" in page_text or "failed to fetch" in page_text or "404" in page_text
    
    take_screenshot(driver, "dashboard_operational", all_found and not has_error)
    save_page_html(driver, "dashboard_operational")
    
    return {
        "status": "PASS" if all_found and not has_error else "FAIL",
        "components": components_found,
        "has_error": has_error
    }

def test_financial_forecasts(driver, frontend_url: str) -> Dict:
    """Testa página /financial-forecasts"""
    print(f"\n📊 Testando /financial-forecasts")
    
    url = f"{frontend_url}/financial-forecasts"
    driver.get(url)
    
    time.sleep(5)
    
    # Verificar erros
    page_text = driver.page_source.lower()
    console_logs = driver.get_log("browser") if hasattr(driver, "get_log") else []
    
    has_cors_error = any("cors" in str(log).lower() for log in console_logs)
    has_network_error = "network error" in page_text or "failed to fetch" in page_text
    has_500_error = "500" in page_text or "internal server error" in page_text
    
    has_error = has_cors_error or has_network_error or has_500_error
    
    take_screenshot(driver, "financial_forecasts", not has_error)
    save_page_html(driver, "financial_forecasts")
    
    # Salvar console logs
    if console_logs:
        with open(OUT_DIR / "financial_forecasts_console.json", "w") as f:
            json.dump([str(log) for log in console_logs], f, indent=2)
    
    return {
        "status": "PASS" if not has_error else "FAIL",
        "has_cors_error": has_cors_error,
        "has_network_error": has_network_error,
        "has_500_error": has_500_error,
        "console_logs": [str(log) for log in console_logs[:10]]  # Primeiros 10
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

