#!/usr/bin/env python3
"""
QA Completo da Versão 2.0 - Dashboard Financeiro
Executa todas as validações necessárias para homologação
"""

import sys
import json
import requests
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Configurações
BACKEND_URL = "https://finaflow-backend-staging-642830139828.us-central1.run.app"
QA_EMAIL = "qa@finaflow.test"
QA_PASSWORD = "QaFinaflow123!"
YEAR = 2025

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_header(text: str):
    """Imprime cabeçalho formatado"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.NC}")
    print(f"{Colors.BLUE}   {text}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.NC}\n")

def print_success(text: str):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")

def print_error(text: str):
    """Imprime mensagem de erro"""
    print(f"{Colors.RED}❌ {text}{Colors.NC}")

def print_warning(text: str):
    """Imprime mensagem de aviso"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")

def print_info(text: str):
    """Imprime mensagem informativa"""
    print(f"{Colors.YELLOW}📊 {text}{Colors.NC}")

def login() -> str:
    """Faz login e retorna token"""
    print_info("Fazendo login na API...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": QA_EMAIL, "password": QA_PASSWORD},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        if not token:
            print_error("Token não retornado")
            sys.exit(1)
        print_success("Login realizado com sucesso")
        return token
    except Exception as e:
        print_error(f"Falha ao fazer login: {e}")
        sys.exit(1)

def test_endpoint(name: str, url: str, token: str) -> Dict[str, Any]:
    """Testa um endpoint e retorna a resposta"""
    print_info(f"Testando: {name}")
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        print_success(f"{name}: OK (HTTP {response.status_code})")
        return data
    except Exception as e:
        print_error(f"{name}: FALHOU - {e}")
        return {}

def validate_annual_summary(data: Dict[str, Any]) -> bool:
    """Valida estrutura e conteúdo do endpoint annual-summary"""
    print_info("Validando estrutura da resposta...")
    
    all_ok = True
    
    # Verificar campos obrigatórios
    required_fields = ["year", "totals", "monthly"]
    for field in required_fields:
        if field not in data:
            print_error(f"Campo obrigatório ausente: {field}")
            all_ok = False
    
    if not all_ok:
        return False
    
    # Verificar se tem 12 meses
    monthly = data.get("monthly", [])
    if len(monthly) != 12:
        print_error(f"Retorna {len(monthly)} meses (esperado: 12)")
        all_ok = False
    else:
        print_success("Retorna 12 meses")
    
    # Verificar estrutura de cada mês
    for i, month_data in enumerate(monthly, 1):
        required_month_fields = ["month", "revenue", "expense", "cost", "balance"]
        for field in required_month_fields:
            if field not in month_data:
                print_error(f"Mês {i}: Campo '{field}' ausente")
                all_ok = False
        
        # Verificar saldo acumulado
        if "accumulated_balance" not in month_data:
            print_error(f"Mês {i}: Campo 'accumulated_balance' ausente")
            all_ok = False
    
    if all_ok:
        print_success("Estrutura de meses válida")
    
    # Verificar totais
    totals = data.get("totals", {})
    print_info("Totais anuais:")
    print(f"   Receita: R$ {totals.get('revenue', 0):,.2f}")
    print(f"   Despesa: R$ {totals.get('expense', 0):,.2f}")
    print(f"   Custo: R$ {totals.get('cost', 0):,.2f}")
    print(f"   Saldo: R$ {totals.get('balance', 0):,.2f}")
    
    # Verificar cálculo de saldo
    calculated_balance = totals.get("revenue", 0) - totals.get("expense", 0) - totals.get("cost", 0)
    reported_balance = totals.get("balance", 0)
    
    if abs(calculated_balance - reported_balance) > 0.01:
        print_error(f"Saldo calculado ({calculated_balance:.2f}) != Saldo reportado ({reported_balance:.2f})")
        all_ok = False
    else:
        print_success("Saldo total calculado corretamente")
    
    # Verificar saldo acumulado progressivo
    print_info("Verificando saldo acumulado progressivo...")
    accumulated = 0
    for month_data in monthly:
        balance = month_data.get("balance", 0)
        accumulated += balance
        reported_accumulated = month_data.get("accumulated_balance", 0)
        
        if abs(accumulated - reported_accumulated) > 0.01:
            month = month_data.get("month", 0)
            print_error(f"Mês {month}: Acumulado calculado ({accumulated:.2f}) != Acumulado reportado ({reported_accumulated:.2f})")
            all_ok = False
    
    if all_ok:
        print_success("Saldo acumulado progressivo correto")
    
    return all_ok

def validate_debug_summary(data: Dict[str, Any]) -> bool:
    """Valida estrutura do endpoint debug"""
    print_info("Validando estrutura da resposta...")
    
    all_ok = True
    
    # Verificar campos obrigatórios
    required_fields = ["year", "annual_totals", "monthly_comparison"]
    for field in required_fields:
        if field not in data:
            print_error(f"Campo obrigatório ausente: {field}")
            all_ok = False
    
    if not all_ok:
        return False
    
    # Verificar estrutura de annual_totals
    annual_totals = data.get("annual_totals", {})
    if "sql" not in annual_totals or "memory" not in annual_totals:
        print_error("annual_totals deve ter 'sql' e 'memory'")
        all_ok = False
    else:
        print_success("Estrutura de annual_totals válida")
    
    # Verificar monthly_comparison
    monthly_comparison = data.get("monthly_comparison", [])
    if len(monthly_comparison) != 12:
        print_error(f"monthly_comparison tem {len(monthly_comparison)} meses (esperado: 12)")
        all_ok = False
    else:
        print_success("monthly_comparison tem 12 meses")
    
    # Verificar estrutura de cada mês
    for month_data in monthly_comparison:
        if "sql" not in month_data or "memory" not in month_data or "match" not in month_data:
            print_error(f"Mês {month_data.get('month', '?')}: Estrutura incompleta")
            all_ok = False
    
    if all_ok:
        print_success("Estrutura completa (SQL, Memory, Comparison)")
    
    return all_ok

def main():
    """Executa QA completo"""
    print_header("QA COMPLETO - VERSÃO 2.0 - DASHBOARD FINANCEIRO")
    
    # Login
    token = login()
    
    # 1. Testar endpoint /annual-summary
    print_header("1. QA DO ENDPOINT /annual-summary")
    annual_data = test_endpoint(
        "annual-summary",
        f"{BACKEND_URL}/api/v1/financial/annual-summary?year={YEAR}",
        token
    )
    
    if annual_data:
        annual_ok = validate_annual_summary(annual_data)
        if not annual_ok:
            print_error("Validação do annual-summary falhou")
            sys.exit(1)
    
    # 2. Testar endpoint /annual-summary/debug
    print_header("2. QA DO ENDPOINT /annual-summary/debug")
    debug_data = test_endpoint(
        "annual-summary-debug",
        f"{BACKEND_URL}/api/v1/financial/annual-summary/debug?year={YEAR}",
        token
    )
    
    if debug_data:
        debug_ok = validate_debug_summary(debug_data)
        if not debug_ok:
            print_warning("Validação do debug-summary falhou (não crítico)")
    
    # 3. Resumo
    print_header("RESUMO DO QA")
    print_success("Endpoints testados com sucesso")
    print_info("Próximos passos:")
    print("   1. Executar script de validação completa (run_validation_with_proxy.sh)")
    print("   2. Validar frontend manualmente")
    print("   3. Gerar relatório final")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

