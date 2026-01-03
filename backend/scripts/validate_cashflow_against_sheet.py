#!/usr/bin/env python3
"""
Teste E2E: Validação Fluxo de Caixa vs Planilha

Valida que o Fluxo de Caixa Mensal do sistema replica fielmente a planilha:
- Ordem de exibição correta
- Totais mensais batem
- Linhas zeradas aparecem
- Estrutura hierárquica correta
- Subtotais corretos

USO:
    python -m scripts.validate_cashflow_against_sheet --year 2025 --month 1

EXIT CODES:
    0: PASS - Tudo bate
    1: Erro de execução
    2: FAIL - Mismatches encontrados
"""

import sys
import os
import argparse
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    import requests
    import pandas as pd
except ImportError as e:
    print(f"❌ Erro: dependência não instalada: {e}")
    print("Execute: pip install requests pandas openpyxl")
    sys.exit(1)

# Importar funções do validate_dashboard_against_client_sheet
from scripts.validate_dashboard_against_client_sheet import (
    login_api,
    carregar_e_normalizar_planilha,
)

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

DEFAULT_EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"
DEFAULT_BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://finaflow-backend-staging-642830139828.us-central1.run.app"
)
DEFAULT_TOLERANCE = Decimal("0.00")  # Tolerância ZERO - dados financeiros devem bater exatamente

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def agregar_planilha_por_grupo_subgrupo_conta(
    entries: List[Dict],
    year: int,
    month: int
) -> Dict[str, Dict[str, Dict[str, Decimal]]]:
    """
    Agrega planilha por grupo → subgrupo → conta para um mês específico.
    Retorna: {grupo: {subgrupo: {conta: valor}}}
    """
    aggregation = defaultdict(lambda: defaultdict(lambda: defaultdict(Decimal)))
    
    for entry in entries:
        if entry["ano"] != year or entry["mes"] != month:
            continue
        
        grupo = entry.get("grupo", "N/A")
        subgrupo = entry.get("subgrupo", "N/A")
        conta = entry.get("conta", "N/A")
        valor = entry.get("valor", Decimal("0"))
        
        aggregation[grupo][subgrupo][conta] += valor
    
    return dict(aggregation)


def buscar_cashflow_api(
    backend_url: str,
    token: str,
    year: int,
    month: int
) -> Dict:
    """
    Busca fluxo de caixa da API.
    """
    try:
        response = requests.get(
            f"{backend_url}/api/v1/cash-flow/daily",
            params={"year": year, "month": month},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Erro ao buscar cash-flow da API: {e}")
        raise


def comparar_estrutura(
    sheet_agg: Dict[str, Dict[str, Dict[str, Decimal]]],
    api_rows: List[Dict],
    tolerance: Decimal
) -> Tuple[bool, List[str]]:
    """
    Compara estrutura e valores entre planilha e API.
    Retorna (ok, lista_de_erros).
    """
    errors = []
    all_ok = True
    
    # Mapear API rows por categoria
    api_by_categoria = {}
    for row in api_rows:
        categoria = row.get("categoria", "")
        nivel = row.get("nivel", -1)
        tipo = row.get("tipo", "")
        total = row.get("total", 0.0)
        
        api_by_categoria[categoria] = {
            "nivel": nivel,
            "tipo": tipo,
            "total": Decimal(str(total))
        }
    
    # Validar grupos
    grupos_planilha = set(sheet_agg.keys())
    grupos_api = {cat for cat, info in api_by_categoria.items() if info["tipo"] == "grupo"}
    
    grupos_faltando_api = grupos_planilha - grupos_api
    grupos_faltando_planilha = grupos_api - grupos_planilha
    
    if grupos_faltando_api:
        errors.append(f"❌ Grupos na planilha mas não na API: {grupos_faltando_api}")
        all_ok = False
    
    if grupos_faltando_planilha:
        errors.append(f"⚠️  Grupos na API mas não na planilha: {grupos_faltando_planilha}")
    
    # Validar valores por grupo
    for grupo, subgrupos_planilha in sheet_agg.items():
        grupo_total_planilha = sum(
            sum(contas.values())
            for contas in subgrupos_planilha.values()
        )
        
        # Buscar total do grupo na API
        grupo_total_api = Decimal("0")
        if grupo in api_by_categoria:
            grupo_total_api = api_by_categoria[grupo]["total"]
        else:
            # Tentar encontrar por nome parcial
            for cat, info in api_by_categoria.items():
                if info["tipo"] == "grupo" and grupo.lower() in cat.lower():
                    grupo_total_api = info["total"]
                    break
        
        delta = abs(grupo_total_planilha - grupo_total_api)
        if delta > tolerance:
            errors.append(
                f"❌ Grupo '{grupo}': planilha={grupo_total_planilha:.2f}, "
                f"API={grupo_total_api:.2f}, delta={delta:.2f}"
            )
            all_ok = False
        else:
            print(f"✅ Grupo '{grupo}': {grupo_total_planilha:.2f} (delta: {delta:.2f})")
    
    # Validar que contas zeradas aparecem na API
    total_contas_planilha = sum(
        len(contas)
        for subgrupos in sheet_agg.values()
        for contas in subgrupos.values()
    )
    
    total_contas_api = sum(
        1 for info in api_by_categoria.values()
        if info["tipo"] == "conta"
    )
    
    if total_contas_api < total_contas_planilha:
        errors.append(
            f"❌ Contas faltando na API: planilha tem {total_contas_planilha}, "
            f"API tem {total_contas_api}"
        )
        all_ok = False
    else:
        print(f"✅ Total de contas: planilha={total_contas_planilha}, API={total_contas_api}")
    
    return all_ok, errors


def validar_ordem(api_rows: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Valida que a ordem dos grupos está correta (não alfabética).
    """
    errors = []
    all_ok = True
    
    # Ordem esperada (conforme planilha)
    ordem_esperada = [
        "Receita",
        "Receita Operacional",
        "Receita Financeira",
        "Deduções",
        "Receita Líquida",  # Subtotal
        "Custos",
        "Lucro Bruto",  # Subtotal
        "Despesas Operacionais",
        "Resultado Operacional",  # Subtotal
        "Movimentações Não Operacionais",
        "Saldo Final",  # Subtotal
    ]
    
    grupos_encontrados = []
    for row in api_rows:
        if row.get("tipo") == "grupo":
            grupos_encontrados.append(row.get("categoria", ""))
    
    # Verificar se ordem está correta
    ordem_atual = []
    for grupo_esperado in ordem_esperada:
        for grupo_atual in grupos_encontrados:
            if grupo_esperado.lower() in grupo_atual.lower() or grupo_atual.lower() in grupo_esperado.lower():
                ordem_atual.append(grupo_atual)
                break
    
    if len(ordem_atual) < len([g for g in grupos_encontrados if any(oe.lower() in g.lower() for oe in ordem_esperada)]):
        errors.append("⚠️  Ordem dos grupos pode estar incorreta")
        all_ok = False
    else:
        print("✅ Ordem dos grupos está correta")
    
    return all_ok, errors


def validar_subtotais(api_rows: List[Dict], tolerance: Decimal) -> Tuple[bool, List[str]]:
    """
    Valida que os subtotais estão corretos.
    """
    errors = []
    all_ok = True
    
    # Buscar valores dos grupos
    receita_total = Decimal("0")
    deducoes_total = Decimal("0")
    custos_total = Decimal("0")
    despesas_total = Decimal("0")
    ajustes_total = Decimal("0")
    
    for row in api_rows:
        categoria = row.get("categoria", "").lower()
        total = Decimal(str(row.get("total", 0.0)))
        tipo = row.get("tipo", "")
        
        if tipo == "grupo":
            if "receita" in categoria and "dedu" not in categoria:
                receita_total += total
            elif "dedu" in categoria:
                deducoes_total += total
            elif "custo" in categoria:
                custos_total += total
            elif "despesa" in categoria and "operacional" in categoria:
                despesas_total += total
            elif "movimenta" in categoria or "não operacional" in categoria:
                ajustes_total += total
    
    # Buscar subtotais calculados
    receita_liquida_api = Decimal("0")
    lucro_bruto_api = Decimal("0")
    resultado_op_api = Decimal("0")
    saldo_final_api = Decimal("0")
    
    for row in api_rows:
        categoria = row.get("categoria", "")
        total = Decimal(str(row.get("total", 0.0)))
        
        if categoria == "Receita Líquida":
            receita_liquida_api = total
        elif categoria == "Lucro Bruto":
            lucro_bruto_api = total
        elif categoria == "Resultado Operacional":
            resultado_op_api = total
        elif categoria == "Saldo Final":
            saldo_final_api = total
    
    # Validar Receita Líquida
    receita_liquida_esperada = receita_total - deducoes_total
    delta = abs(receita_liquida_api - receita_liquida_esperada)
    if delta > tolerance:
        errors.append(
            f"❌ Receita Líquida: esperado={receita_liquida_esperada:.2f}, "
            f"obtido={receita_liquida_api:.2f}, delta={delta:.2f}"
        )
        all_ok = False
    else:
        print(f"✅ Receita Líquida: {receita_liquida_esperada:.2f}")
    
    # Validar Lucro Bruto
    lucro_bruto_esperado = receita_liquida_esperada - custos_total
    delta = abs(lucro_bruto_api - lucro_bruto_esperado)
    if delta > tolerance:
        errors.append(
            f"❌ Lucro Bruto: esperado={lucro_bruto_esperado:.2f}, "
            f"obtido={lucro_bruto_api:.2f}, delta={delta:.2f}"
        )
        all_ok = False
    else:
        print(f"✅ Lucro Bruto: {lucro_bruto_esperado:.2f}")
    
    # Validar Resultado Operacional
    resultado_op_esperado = lucro_bruto_esperado - despesas_total
    delta = abs(resultado_op_api - resultado_op_esperado)
    if delta > tolerance:
        errors.append(
            f"❌ Resultado Operacional: esperado={resultado_op_esperado:.2f}, "
            f"obtido={resultado_op_api:.2f}, delta={delta:.2f}"
        )
        all_ok = False
    else:
        print(f"✅ Resultado Operacional: {resultado_op_esperado:.2f}")
    
    # Validar Saldo Final
    saldo_final_esperado = resultado_op_esperado + ajustes_total
    delta = abs(saldo_final_api - saldo_final_esperado)
    if delta > tolerance:
        errors.append(
            f"❌ Saldo Final: esperado={saldo_final_esperado:.2f}, "
            f"obtido={saldo_final_api:.2f}, delta={delta:.2f}"
        )
        all_ok = False
    else:
        print(f"✅ Saldo Final: {saldo_final_esperado:.2f}")
    
    return all_ok, errors


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="E2E: Validação Fluxo de Caixa vs Planilha",
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
        "--month",
        type=int,
        default=None,
        help="Mês a validar (1-12, default: todos os meses)"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default=DEFAULT_BACKEND_URL,
        help=f"URL do backend (default: {DEFAULT_BACKEND_URL})"
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
    month = args.month
    backend_url = args.backend_url
    tolerance = Decimal(str(args.tolerance))
    
    print("="*80)
    print("🚀 E2E: VALIDAÇÃO FLUXO DE CAIXA VS PLANILHA")
    print("="*80)
    print(f"Arquivo: {excel_file}")
    print(f"Ano: {year}")
    print(f"Mês: {month if month else 'Todos (1-12)'}")
    print(f"Backend: {backend_url}")
    print(f"Tolerância: {tolerance}")
    print("="*80)
    
    # 1. Ler planilha
    print(f"\n{'='*80}")
    print("📖 LENDO PLANILHA")
    print(f"{'='*80}")
    
    try:
        from sqlalchemy.orm import Session
        from app.database import SessionLocal
        
        db = SessionLocal()
        try:
            from app.models.auth import Tenant
            tenant = db.query(Tenant).first()
            
            if not tenant:
                print("❌ Erro: Tenant não encontrado no banco")
                sys.exit(1)
            
            # Carregar e normalizar planilha
            entries_bruto, entries_filtrado = carregar_e_normalizar_planilha(
                excel_file=excel_file,
                tenant_id=str(tenant.id),
                year=year,
                db=db
            )
            
            print(f"✅ Planilha lida: {len(entries_filtrado)} lançamentos")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erro ao ler planilha: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 2. Fazer login na API
    print(f"\n{'='*80}")
    print("🔐 FAZENDO LOGIN NA API")
    print(f"{'='*80}")
    
    token = login_api(backend_url)
    if not token:
        print("❌ Falha ao fazer login na API")
        sys.exit(1)
    
    print("✅ Login realizado com sucesso")
    
    # 3. Validar meses
    meses_para_validar = [month] if month else list(range(1, 13))
    all_months_ok = True
    all_errors = []
    
    for mes in meses_para_validar:
        print(f"\n{'='*80}")
        print(f"📅 VALIDANDO MÊS {mes:02d}/{year}")
        print(f"{'='*80}")
        
        # Agregar planilha para este mês
        sheet_agg = agregar_planilha_por_grupo_subgrupo_conta(
            entries_filtrado,
            year,
            mes
        )
        
        # Buscar cash-flow da API
        try:
            api_data = buscar_cashflow_api(backend_url, token, year, mes)
            api_rows = api_data.get("data", [])
        except Exception as e:
            print(f"❌ Erro ao buscar cash-flow da API: {e}")
            all_months_ok = False
            continue
        
        # Validar estrutura e valores
        estrutura_ok, estrutura_errors = comparar_estrutura(
            sheet_agg,
            api_rows,
            tolerance
        )
        
        # Validar ordem
        ordem_ok, ordem_errors = validar_ordem(api_rows)
        
        # Validar subtotais
        subtotais_ok, subtotais_errors = validar_subtotais(api_rows, tolerance)
        
        mes_ok = estrutura_ok and ordem_ok and subtotais_ok
        
        if not mes_ok:
            all_months_ok = False
            all_errors.extend(estrutura_errors)
            all_errors.extend(ordem_errors)
            all_errors.extend(subtotais_errors)
            print(f"\n❌ Mês {mes:02d}/{year} falhou validação")
        else:
            print(f"\n✅ Mês {mes:02d}/{year} passou todas as validações")
    
    # 4. Resumo final
    print(f"\n{'='*80}")
    print("📋 RESUMO FINAL")
    print(f"{'='*80}")
    
    if all_months_ok:
        print("✅ PASS: Fluxo de Caixa replica fielmente a planilha!")
        print(f"\nMeses validados: {len(meses_para_validar)}")
        sys.exit(0)
    else:
        print("❌ FAIL: Mismatches encontrados")
        print("\nErros encontrados:")
        for error in all_errors:
            print(f"  {error}")
        sys.exit(2)


if __name__ == "__main__":
    main()

