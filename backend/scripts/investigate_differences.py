#!/usr/bin/env python3
"""
Script de Investigação Detalhada de Diferenças

Analisa linha a linha as diferenças entre planilha e sistema para identificar:
- Lançamentos duplicados
- Lançamentos faltantes
- Classificações incorretas
- Valores divergentes

USO:
    python -m scripts.investigate_differences --year 2025 --type despesa
"""

import sys
import os
import argparse
import json
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    import pandas as pd
    import requests
except ImportError as e:
    print(f"❌ Erro: dependência não instalada: {e}")
    print("Execute: pip install pandas openpyxl requests")
    sys.exit(1)

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

DEFAULT_EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"
DEFAULT_BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://finaflow-backend-staging-642830139828.us-central1.run.app"
)

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def parse_currency(value) -> Decimal:
    """Converte valor para Decimal"""
    if pd.isna(value) or value == "" or value is None:
        return Decimal("0.00")
    
    value_str = str(value).strip()
    value_str = value_str.replace("R$", "").replace("$", "").strip()
    value_str = value_str.replace(".", "").replace(",", ".")
    
    try:
        return Decimal(value_str)
    except:
        return Decimal("0.00")


def login_api(username: str = "qa@finaflow.test", password: str = "QaFinaflow123!") -> str:
    """Faz login na API e retorna o token"""
    try:
        resp = requests.post(
            f"{DEFAULT_BACKEND_URL}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
        else:
            print(f"❌ Erro no login: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        return None


def get_monthly_transactions_from_api(token: str, year: int, month: int, transaction_type: str = None) -> List[Dict]:
    """Obtém todas as transações mensais da API (com paginação)"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        all_items = []
        page = 1
        page_size = 200  # Máximo permitido
        
        while True:
            url = f"{DEFAULT_BACKEND_URL}/api/v1/financial/monthly-transactions?year={year}&month={month}&page={page}&page_size={page_size}"
            if transaction_type:
                url += f"&type={transaction_type.upper()}"
            
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"❌ Erro ao buscar monthly transactions (página {page}): {resp.status_code}")
                if resp.status_code == 422:
                    print(f"   Detalhes: {resp.text}")
                break
            
            data = resp.json()
            items = data.get("items", [])
            all_items.extend(items)
            
            # Verificar se há mais páginas
            total_pages = data.get("total_pages", 1)
            if page >= total_pages:
                break
            
            page += 1
        
        return all_items
    except Exception as e:
        print(f"❌ Erro ao buscar monthly transactions: {e}")
        return []


def extract_fluxo_caixa_detailed(excel_file: Path, transaction_type: str = None, use_totals_only: bool = True) -> Dict[int, List[Dict]]:
    """
    Extrai lançamentos detalhados da aba "Fluxo de caixa-2025"
    
    Se use_totals_only=True, extrai apenas os totais principais (linha "Despesas Operacionais", etc.)
    Se use_totals_only=False, extrai subitens individuais (pode incluir duplicações)
    
    Retorna:
        {
            mes: [
                {
                    "categoria": str,
                    "subcategoria": str,
                    "valor_realizado": Decimal,
                    "valor_previsto": Decimal
                }
            ]
        }
    """
    print(f"📊 Extraindo dados detalhados da planilha (tipo: {transaction_type or 'todos'}, totals_only={use_totals_only})...")
    
    try:
        df = pd.read_excel(excel_file, sheet_name="Fluxo de caixa-2025", header=None)
    except Exception as e:
        print(f"❌ Erro ao ler planilha: {e}")
        return {}
    
    # Estrutura: colunas Realizado = 3, 7, 11, 15, etc.
    month_cols = {m + 1: 3 + (m * 4) for m in range(12)}
    
    detailed_data = {month: [] for month in range(1, 13)}
    
    # Se usar apenas totais, extrair apenas as linhas principais
    if use_totals_only:
        for idx in range(len(df)):
            row = df.iloc[idx]
            if len(row) < 2:
                continue
            
            col1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            col1_upper = col1.upper()
            
            # Identificar apenas linhas de TOTAIS principais
            category = None
            if col1_upper == "RECEITA":
                category = "Receita"
                current_type = "receita"
            elif col1_upper in ["DESPESAS OPERACIONAIS", "DESPESAS", "DESPESA"]:
                category = "Despesas Operacionais"
                current_type = "despesa"
            elif col1_upper in ["CUSTOS", "CUSTO"]:
                category = "Custos"
                current_type = "custo"
            
            # Se encontrou uma linha de total principal e corresponde ao tipo solicitado
            if category and (transaction_type is None or current_type == transaction_type.lower()):
                for month in range(1, 13):
                    col_realizado = month_cols.get(month)
                    if col_realizado and col_realizado < len(row):
                        valor = row.iloc[col_realizado]
                        if pd.notna(valor) and isinstance(valor, (int, float)) and valor != 0:
                            try:
                                valor_decimal = Decimal(str(valor))
                                detailed_data[month].append({
                                    "categoria": category,
                                    "subcategoria": category,  # Mesmo valor para totais
                                    "valor_realizado": valor_decimal,
                                    "linha_planilha": idx + 1
                                })
                            except:
                                pass
        return detailed_data
    
    # Mapear tipos de transação
    type_keywords = {
        "receita": ["receita"],
        "despesa": ["despesa", "despesas operacionais"],
        "custo": ["custo", "custos"]
    }
    
    # Linhas que devem ser IGNORADAS (totalizadores, saldos, cálculos)
    IGNORE_KEYWORDS = [
        "LUCRO BRUTO",
        "LUCRO ANTES DOS INVESTIMENTOS",
        "DESEMBOLSO TOTAL",
        "LUCRO OPERACIONAL",
        "LUCRO LÍQUIDO DE CAIXA MENSAL",
        "LUCRO LÍQUIDO ACUMULADO",
        "LUCRO LIQUIDO ACUMULADO",
        "SALDO DO ANO ANTERIOR",
        "SALDO ANTERIOR",
        "RECEITA LÍQUIDA",
        "RESULTADO OPERACIONAL",
        "DISTRIBUIÇÃO DE LUCROS",
        "INVESTIMENTOS",  # Grupo de investimentos (não são despesas/custos)
        "INVESTIMENTOS EM BENS MATERIAIS",  # Subgrupo de investimentos
        "OUTROS INVESTIMENTOS",
    ]
    
    current_type = None
    current_category = None
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        if len(row) < 2:
            continue
        
        col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        
        # IGNORAR linhas de totalizadores e saldos
        col1_upper = col1.upper()
        if any(keyword in col1_upper for keyword in IGNORE_KEYWORDS):
            continue
        
        # Identificar tipo principal
        if col1_upper == "RECEITA":
            current_type = "receita"
            current_category = "Receita"
        elif col1_upper in ["DESPESA", "DESPESAS", "DESPESAS OPERACIONAIS"]:
            current_type = "despesa"
            current_category = "Despesas Operacionais"
        elif col1_upper in ["CUSTO", "CUSTOS"]:
            current_type = "custo"
            current_category = "Custos"
        elif col1_upper in ["TOTAL", "SALDO", "LUCRO"]:
            # Ignorar linhas genéricas de total/saldo/lucro que não foram capturadas acima
            current_type = None
            current_category = None
            continue
        
        # Se estamos em uma categoria de interesse e há filtro de tipo
        if current_type and (transaction_type is None or current_type == transaction_type.lower()):
            # IGNORAR linhas que são apenas o nome do grupo (totalizadores)
            # Exemplo: "Despesas Operacionais" sem subcategoria específica
            # Essas linhas são totalizadores, não lançamentos individuais
            if col1_upper in ["DESPESAS OPERACIONAIS", "DESPESAS", "CUSTOS", "CUSTO", "RECEITA"]:
                # Esta linha é apenas o cabeçalho/totalizador do grupo
                continue
            
            # IGNORAR grupos de movimentações não operacionais (não são despesas reais)
            if "MOVIMENTAÇÕES NÃO OPERACIONAIS" in col1_upper or "MOVIMENTACOES NAO OPERACIONAIS" in col1_upper:
                continue
            
            # Extrair valores para cada mês
            for month in range(1, 13):
                col_realizado = month_cols.get(month)
                if col_realizado and col_realizado < len(row):
                    valor = row.iloc[col_realizado]
                    if pd.notna(valor) and isinstance(valor, (int, float)) and valor != 0:
                        try:
                            valor_decimal = Decimal(str(valor))
                            detailed_data[month].append({
                                "categoria": current_category,
                                "subcategoria": col1 if col1 else col0,
                                "valor_realizado": valor_decimal,
                                "linha_planilha": idx + 1
                            })
                        except:
                            pass
    
    return detailed_data


def get_system_transactions_by_month(token: str, year: int, month: int, transaction_type: str = None) -> List[Dict]:
    """Obtém todas as transações do sistema para um mês específico"""
    transactions = get_monthly_transactions_from_api(token, year, month, transaction_type)
    return transactions


def compare_detailed_month(
    excel_data: List[Dict],
    system_data: List[Dict],
    month: int,
    transaction_type: str
) -> Dict:
    """Compara dados detalhados de um mês"""
    
    # Agrupar por categoria/subcategoria
    excel_by_category = defaultdict(Decimal)
    for item in excel_data:
        key = f"{item['categoria']}::{item['subcategoria']}"
        excel_by_category[key] += item["valor_realizado"]
    
    system_by_category = defaultdict(Decimal)
    for item in system_data:
        # API retorna: group, subgroup, amount (não grupo.name, subgrupo.name, valor)
        grupo = item.get("group") or "N/A"
        subgrupo = item.get("subgroup") or "N/A"
        key = f"{grupo}::{subgrupo}"
        # amount vem como string
        amount_str = item.get("amount", "0")
        try:
            valor = Decimal(str(amount_str))
        except:
            valor = Decimal("0")
        system_by_category[key] += valor
    
    # Comparar
    differences = []
    all_keys = set(excel_by_category.keys()) | set(system_by_category.keys())
    
    for key in all_keys:
        excel_val = excel_by_category.get(key, Decimal("0"))
        system_val = system_by_category.get(key, Decimal("0"))
        diff = excel_val - system_val
        
        if diff != 0:
            differences.append({
                "categoria": key,
                "excel": float(excel_val),
                "sistema": float(system_val),
                "diff": float(diff)
            })
    
    return {
        "month": month,
        "type": transaction_type,
        "excel_total": float(sum(excel_by_category.values())),
        "system_total": float(sum(system_by_category.values())),
        "total_diff": float(sum(excel_by_category.values()) - sum(system_by_category.values())),
        "differences": differences,
        "excel_items": len(excel_data),
        "system_items": len(system_data)
    }


def detect_duplicates(transactions: List[Dict]) -> List[Dict]:
    """Detecta transações duplicadas"""
    duplicates = []
    
    # Agrupar por valor + data + tipo + grupo + subgrupo
    seen = {}
    
    for tx in transactions:
        # API retorna: amount (string), date, type, group, subgroup
        amount_str = tx.get("amount", "0")
        try:
            valor = Decimal(str(amount_str))
        except:
            valor = Decimal("0")
        
        data = tx.get("date", "")
        tipo = tx.get("type", "")
        grupo = tx.get("group") or ""
        subgrupo = tx.get("subgroup") or ""
        
        # Ignorar transações com valor zero na detecção de duplicatas
        if valor == 0:
            continue
        
        key = (valor, data, tipo, grupo, subgrupo)
        
        if key in seen:
            if key not in [d["key"] for d in duplicates]:
                duplicates.append({
                    "key": key,
                    "valor": float(valor),
                    "data": data,
                    "tipo": tipo,
                    "grupo": grupo,
                    "subgrupo": subgrupo,
                    "count": 2,
                    "ids": [seen[key]["id"], tx.get("id", "N/A")]
                })
            else:
                # Incrementar contador
                for dup in duplicates:
                    if dup["key"] == key:
                        dup["count"] += 1
                        dup["ids"].append(tx.get("id", "N/A"))
        else:
            seen[key] = {
                "id": tx.get("id", "N/A"),
                "tx": tx
            }
    
    return duplicates


def main():
    parser = argparse.ArgumentParser(description="Investigação Detalhada de Diferenças")
    parser.add_argument("--year", type=int, default=2025, help="Ano para investigação")
    parser.add_argument("--type", type=str, choices=["receita", "despesa", "custo"], help="Tipo de transação")
    parser.add_argument("--month", type=int, help="Mês específico (1-12)")
    parser.add_argument("--output", type=str, default=None, help="Arquivo JSON de saída")
    
    args = parser.parse_args()
    
    excel_file = Path(DEFAULT_EXCEL_FILE)
    if not excel_file.exists():
        print(f"❌ Arquivo não encontrado: {excel_file}")
        sys.exit(1)
    
    print("🔍 Iniciando investigação detalhada...")
    print(f"   Ano: {args.year}")
    print(f"   Tipo: {args.type or 'todos'}")
    print(f"   Mês: {args.month or 'todos'}")
    
    # 1. Extrair dados da planilha
    print("\n1️⃣ Extraindo dados da planilha...")
    excel_detailed = extract_fluxo_caixa_detailed(excel_file, args.type)
    
    # 2. Conectar à API
    print("\n2️⃣ Conectando à API...")
    token = login_api()
    if not token:
        print("❌ Não foi possível fazer login")
        sys.exit(1)
    
    # 3. Investigar mês a mês
    print("\n3️⃣ Investigando diferenças...")
    investigation_results = {
        "year": args.year,
        "type": args.type,
        "monthly_analysis": [],
        "duplicates": [],
        "summary": {}
    }
    
    months_to_check = [args.month] if args.month else range(1, 13)
    
    for month in months_to_check:
        print(f"\n   📅 Mês {month}...")
        
        # Dados da planilha
        excel_month_data = excel_detailed.get(month, [])
        
        # Dados do sistema
        system_transactions = get_system_transactions_by_month(token, args.year, month, args.type)
        
        # Comparar
        comparison = compare_detailed_month(
            excel_month_data,
            system_transactions,
            month,
            args.type or "todos"
        )
        
        investigation_results["monthly_analysis"].append(comparison)
        
        # Detectar duplicatas
        if system_transactions:
            month_duplicates = detect_duplicates(system_transactions)
            for dup in month_duplicates:
                dup["month"] = month
                investigation_results["duplicates"].append(dup)
    
    # 4. Resumo
    total_excel = sum(c["excel_total"] for c in investigation_results["monthly_analysis"])
    total_system = sum(c["system_total"] for c in investigation_results["monthly_analysis"])
    total_diff = total_excel - total_system
    
    investigation_results["summary"] = {
        "total_excel": float(total_excel),
        "total_system": float(total_system),
        "total_diff": float(total_diff),
        "total_duplicates": len(investigation_results["duplicates"])
    }
    
    # 5. Relatório
    print("\n" + "=" * 80)
    print("📋 RELATÓRIO DE INVESTIGAÇÃO")
    print("=" * 80)
    print(f"\n📊 Resumo:")
    print(f"   Total Planilha: R$ {total_excel:,.2f}")
    print(f"   Total Sistema: R$ {total_system:,.2f}")
    print(f"   Diferença Total: R$ {total_diff:,.2f}")
    print(f"   Duplicatas Encontradas: {len(investigation_results['duplicates'])}")
    
    if investigation_results["duplicates"]:
        print(f"\n⚠️  DUPLICATAS ENCONTRADAS:")
        for dup in investigation_results["duplicates"][:10]:
            print(f"   - Mês {dup['month']}: {dup['count']}x R$ {dup['valor']:,.2f} em {dup['data']} ({dup['tipo']})")
            print(f"     IDs: {', '.join(dup['ids'][:3])}")
    
    print("\n📊 Diferenças por Mês:")
    for analysis in investigation_results["monthly_analysis"]:
        if analysis["total_diff"] != 0:
            month_name = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
                         "Jul", "Ago", "Set", "Out", "Nov", "Dez"][analysis["month"]]
            print(f"\n   {month_name}/{args.year}:")
            print(f"     Planilha: R$ {analysis['excel_total']:,.2f}")
            print(f"     Sistema: R$ {analysis['system_total']:,.2f}")
            print(f"     Diferença: R$ {analysis['total_diff']:,.2f}")
            print(f"     Itens Planilha: {analysis['excel_items']}")
            print(f"     Itens Sistema: {analysis['system_items']}")
            
            if analysis["differences"]:
                print(f"     Principais diferenças por categoria:")
                for diff in analysis["differences"][:5]:
                    print(f"       - {diff['categoria']}: Planilha R$ {diff['excel']:,.2f} | Sistema R$ {diff['sistema']:,.2f} | Diff R$ {diff['diff']:,.2f}")
    
    # 6. Salvar JSON
    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(investigation_results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Relatório salvo em: {output_file}")
    
    print("\n" + "=" * 80)
    
    # Exit code
    if total_diff != 0 or investigation_results["duplicates"]:
        print("\n❌ FALHA: Diferenças ou duplicatas encontradas!")
        sys.exit(2)
    else:
        print("\n✅ Investigação OK - Sem diferenças ou duplicatas!")
        sys.exit(0)


if __name__ == "__main__":
    main()

