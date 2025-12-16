#!/usr/bin/env python3
"""
Script E2E: Validação Planilha → API

Valida que os números da planilha do cliente estão replicados corretamente na API.

USO:
    python -m scripts.e2e_sheet_to_api --file data/fluxo_caixa_2025.xlsx --year 2025

EXIT CODES:
    0: PASS - Todos os valores batem
    1: Erro de execução
    2: FAIL - Mismatch encontrado
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from decimal import Decimal
from typing import Dict, Optional
from collections import defaultdict

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    import requests
except ImportError:
    print("❌ Erro: dependência não instalada: requests")
    print("Execute: pip install requests")
    sys.exit(1)

# Importar funções do validate_dashboard_against_client_sheet
from scripts.validate_dashboard_against_client_sheet import (
    login_api,
    consumir_api,
    carregar_e_normalizar_planilha,
    agregar_planilha_filtrada,
    MonthlySummary
)

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

DEFAULT_EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"
DEFAULT_BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://finaflow-backend-staging-642830139828.us-central1.run.app"
)
DEFAULT_TOLERANCE = Decimal("0.01")  # 1 centavo

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def executar_seed(excel_file: Path, year: int) -> bool:
    """
    Executa o seed a partir do arquivo Excel.
    Retorna True se sucesso, False caso contrário.
    """
    print(f"\n{'='*80}")
    print("📥 EXECUTANDO SEED")
    print(f"{'='*80}")
    print(f"Arquivo: {excel_file}")
    print(f"Ano: {year}")
    
    try:
        # Executar seed via subprocess
        cmd = [
            sys.executable,
            "-m", "scripts.seed_from_client_sheet",
            "--file", str(excel_file),
            "--year", str(year)
        ]
        
        result = subprocess.run(
            cmd,
            cwd=str(backend_path),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos
        )
        
        if result.returncode != 0:
            print(f"❌ Erro ao executar seed:")
            print(result.stderr)
            return False
        
        print("✅ Seed executado com sucesso")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao executar seed (mais de 5 minutos)")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar seed: {e}")
        return False

def calcular_totais_anuais(summary: MonthlySummary, year: int) -> Dict[str, Decimal]:
    """
    Calcula totais anuais a partir do resumo mensal.
    """
    totais = {
        "receita": Decimal("0"),
        "despesa": Decimal("0"),
        "custo": Decimal("0"),
        "saldo": Decimal("0")
    }
    
    for (ano, mes), valores in summary.items():
        if ano == year:
            totais["receita"] += valores["receita"]
            totais["despesa"] += valores["despesa"]
            totais["custo"] += valores["custo"]
            totais["saldo"] += valores["saldo"]
    
    return totais

def comparar_valores(
    esperado: Decimal,
    obtido: Decimal,
    tipo: str,
    mes: Optional[int] = None,
    tolerance: Decimal = DEFAULT_TOLERANCE
) -> tuple[bool, Decimal]:
    """
    Compara dois valores com tolerância.
    Retorna (ok, delta).
    """
    delta = abs(esperado - obtido)
    ok = delta <= tolerance
    
    if not ok:
        prefix = f"MES={year:04d}-{mes:02d} " if mes else ""
        print(f"❌ {prefix}TIPO={tipo} esperado={esperado:.2f} obtido={obtido:.2f} delta={delta:.2f}")
    
    return ok, delta

def validar_totais_anuais(
    sheet_totals: Dict[str, Decimal],
    api_totals: Dict[str, Decimal],
    tolerance: Decimal
) -> bool:
    """
    Valida totais anuais.
    Retorna True se tudo ok.
    """
    print(f"\n{'='*80}")
    print("📊 VALIDANDO TOTAIS ANUAIS")
    print(f"{'='*80}")
    
    all_ok = True
    
    for tipo in ["receita", "despesa", "custo", "saldo"]:
        esperado = sheet_totals.get(tipo, Decimal("0"))
        obtido = api_totals.get(tipo, Decimal("0"))
        ok, delta = comparar_valores(esperado, obtido, tipo.upper(), year, tolerance=tolerance)
        if ok:
            print(f"✅ {tipo.upper()}: {esperado:.2f} (delta: {delta:.2f})")
        else:
            all_ok = False
    
    return all_ok

def validar_meses(
    sheet_summary: MonthlySummary,
    api_summary: MonthlySummary,
    year: int,
    tolerance: Decimal,
    meses_verificar: list = [1, 6, 12]
) -> bool:
    """
    Valida valores mensais.
    Retorna True se tudo ok.
    """
    print(f"\n{'='*80}")
    print("📅 VALIDANDO MESES")
    print(f"{'='*80}")
    
    all_ok = True
    
    for mes in meses_verificar:
        key = (year, mes)
        sheet_vals = sheet_summary.get(key, {
            "receita": Decimal("0"),
            "despesa": Decimal("0"),
            "custo": Decimal("0"),
            "saldo": Decimal("0")
        })
        api_vals = api_summary.get(key, {
            "receita": Decimal("0"),
            "despesa": Decimal("0"),
            "custo": Decimal("0"),
            "saldo": Decimal("0")
        })
        
        print(f"\n📆 Mês {mes:02d}/{year}:")
        
        for tipo in ["receita", "despesa", "custo", "saldo"]:
            esperado = sheet_vals.get(tipo, Decimal("0"))
            obtido = api_vals.get(tipo, Decimal("0"))
            ok, delta = comparar_valores(esperado, obtido, tipo.upper(), year, mes, tolerance)
            if ok:
                print(f"  ✅ {tipo.upper()}: {esperado:.2f}")
            else:
                all_ok = False
        
        # Validar saldo acumulado (se disponível na API)
        # Nota: O saldo acumulado não está na planilha, então não validamos aqui
    
    return all_ok

def validar_todos_meses(
    sheet_summary: MonthlySummary,
    api_summary: MonthlySummary,
    year: int,
    tolerance: Decimal
) -> bool:
    """
    Valida todos os 12 meses.
    Retorna True se tudo ok.
    """
    print(f"\n{'='*80}")
    print("📅 VALIDANDO TODOS OS 12 MESES")
    print(f"{'='*80}")
    
    all_ok = True
    meses_com_erro = []
    
    for mes in range(1, 13):
        key = (year, mes)
        sheet_vals = sheet_summary.get(key, {
            "receita": Decimal("0"),
            "despesa": Decimal("0"),
            "custo": Decimal("0"),
            "saldo": Decimal("0")
        })
        api_vals = api_summary.get(key, {
            "receita": Decimal("0"),
            "despesa": Decimal("0"),
            "custo": Decimal("0"),
            "saldo": Decimal("0")
        })
        
        mes_ok = True
        for tipo in ["receita", "despesa", "custo", "saldo"]:
            esperado = sheet_vals.get(tipo, Decimal("0"))
            obtido = api_vals.get(tipo, Decimal("0"))
            ok, _ = comparar_valores(esperado, obtido, tipo.upper(), year, mes, tolerance)
            if not ok:
                mes_ok = False
                all_ok = False
        
        if not mes_ok:
            meses_com_erro.append(mes)
    
    if meses_com_erro:
        print(f"\n❌ Meses com erro: {meses_com_erro}")
    else:
        print(f"\n✅ Todos os 12 meses estão consistentes")
    
    return all_ok

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="E2E: Validação Planilha → API",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_EXCEL_FILE,
        help=f"Arquivo Excel (default: {DEFAULT_EXCEL_FILE})"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Ano a validar (default: 2025)"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default=DEFAULT_BACKEND_URL,
        help=f"URL do backend (default: {DEFAULT_BACKEND_URL})"
    )
    parser.add_argument(
        "--run-seed",
        action="store_true",
        default=True,
        help="Executar seed antes de validar (default: True)"
    )
    parser.add_argument(
        "--no-seed",
        dest="run_seed",
        action="store_false",
        help="Não executar seed (usar dados existentes)"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=float(DEFAULT_TOLERANCE),
        help=f"Tolerância para comparação em centavos (default: {DEFAULT_TOLERANCE})"
    )
    
    args = parser.parse_args()
    
    excel_file = args.file
    year = args.year
    backend_url = args.backend_url
    run_seed = args.run_seed
    tolerance = Decimal(str(args.tolerance))
    
    print("="*80)
    print("🚀 E2E: VALIDAÇÃO PLANILHA → API")
    print("="*80)
    print(f"Arquivo: {excel_file}")
    print(f"Ano: {year}")
    print(f"Backend: {backend_url}")
    print(f"Executar seed: {run_seed}")
    print(f"Tolerância: {tolerance}")
    print("="*80)
    
    # 1. Executar seed se solicitado
    if run_seed:
        if not executar_seed(excel_file, year):
            print("\n❌ Falha ao executar seed")
            sys.exit(1)
    else:
        print("\n⏭️  Pulando seed (usando dados existentes)")
    
    # 2. Ler planilha e agregar (usando funções existentes)
    print(f"\n{'='*80}")
    print("📖 LENDO PLANILHA E AGREGANDO")
    print(f"{'='*80}")
    
    try:
        from sqlalchemy.orm import Session
        from app.database import SessionLocal
        
        db = SessionLocal()
        try:
            # Obter tenant e business_unit padrão
            from app.models.auth import Tenant, BusinessUnit
            tenant = db.query(Tenant).first()
            business_unit = db.query(BusinessUnit).first()
            
            if not tenant or not business_unit:
                print("❌ Erro: Tenant ou BusinessUnit não encontrados no banco")
                sys.exit(1)
            
            # Carregar e normalizar planilha (retorna entries_bruto e entries_filtrado)
            entries_bruto, entries_filtrado = carregar_e_normalizar_planilha(
                excel_file=excel_file,
                tenant_id=str(tenant.id),
                year=year,
                db=db
            )
            
            # Agregar planilha filtrada
            sheet_summary = agregar_planilha_filtrada(entries_filtrado, year)
            
            print(f"✅ Planilha lida: {len(entries_filtrado)} lançamentos")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erro ao ler planilha: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 3. Fazer login na API
    print(f"\n{'='*80}")
    print("🔐 FAZENDO LOGIN NA API")
    print(f"{'='*80}")
    
    token = login_api(backend_url)
    if not token:
        print("❌ Falha ao fazer login na API")
        sys.exit(1)
    
    print("✅ Login realizado com sucesso")
    
    # 4. Consumir API
    print(f"\n{'='*80}")
    print("📡 CONSUMINDO API")
    print(f"{'='*80}")
    
    api_summary = consumir_api(backend_url, year, token)
    if not api_summary:
        print("❌ Falha ao consumir API")
        sys.exit(1)
    
    print("✅ API consumida com sucesso")
    
    # 5. Calcular totais anuais
    sheet_totals = calcular_totais_anuais(sheet_summary, year)
    api_totals = calcular_totais_anuais(api_summary, year)
    
    # 6. Validar totais anuais
    totais_ok = validar_totais_anuais(sheet_totals, api_totals, tolerance)
    
    # 7. Validar todos os 12 meses
    meses_ok = validar_todos_meses(sheet_summary, api_summary, year, tolerance)
    
    # 8. Validar 3 meses específicos (Jan, Jun, Dez)
    meses_especificos_ok = validar_meses(
        sheet_summary,
        api_summary,
        year,
        tolerance,
        meses_verificar=[1, 6, 12]
    )
    
    # 9. Resumo final
    print(f"\n{'='*80}")
    print("📋 RESUMO FINAL")
    print(f"{'='*80}")
    
    if totais_ok and meses_ok:
        print("✅ PASS: Todos os valores batem!")
        print(f"\nTotais Anuais:")
        print(f"  Receita: {sheet_totals['receita']:.2f}")
        print(f"  Despesa: {sheet_totals['despesa']:.2f}")
        print(f"  Custo: {sheet_totals['custo']:.2f}")
        print(f"  Saldo: {sheet_totals['saldo']:.2f}")
        print(f"\nMeses verificados: Jan, Jun, Dez")
        sys.exit(0)
    else:
        print("❌ FAIL: Mismatches encontrados")
        if not totais_ok:
            print("  - Totais anuais não batem")
        if not meses_ok:
            print("  - Alguns meses não batem")
        sys.exit(2)

if __name__ == "__main__":
    main()

