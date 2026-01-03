#!/usr/bin/env python3
"""
Lista todas as contas únicas dos lançamentos diários para identificar
contas de disponibilidade que podem ter nomes diferentes.
"""

import sys
from pathlib import Path
import pandas as pd
from collections import Counter

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"

def find_sheet_in_excel(excel_file: Path, sheet_names: list) -> str:
    try:
        xls = pd.ExcelFile(excel_file)
        for name in sheet_names:
            if name in xls.sheet_names:
                return name
    except Exception as e:
        print(f"❌ Erro: {e}")
    return None

def main():
    print("="*80)
    print("📋 TODAS AS CONTAS DOS LANÇAMENTOS DIÁRIOS")
    print("="*80)
    
    sheet_names = ["Lançamento Diário", "Lançamento Diario", "Lancamento Diario"]
    sheet_name = find_sheet_in_excel(EXCEL_FILE, sheet_names)
    if not sheet_name:
        print("❌ Aba não encontrada")
        return
    
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
    df.columns = df.columns.str.strip()
    
    # Encontrar coluna de conta
    conta_col = None
    for col in df.columns:
        if 'conta' in col.lower():
            conta_col = col
            break
    
    if not conta_col:
        print("❌ Coluna 'conta' não encontrada")
        return
    
    # Contar ocorrências de cada conta
    contas = df[conta_col].dropna().astype(str).str.strip()
    contas_count = Counter(contas)
    
    print(f"\nTotal de contas únicas: {len(contas_count)}\n")
    print("="*80)
    print("📊 CONTAS (ordenadas por frequência):")
    print("="*80)
    
    for conta, count in contas_count.most_common():
        print(f"  • {conta} ({count} lançamentos)")
    
    print("\n" + "="*80)
    print("💡 CONTAS QUE PODEM SER DE DISPONIBILIDADE:")
    print("="*80)
    
    # Palavras-chave que podem indicar disponibilidade
    keywords = ["banco", "banc", "caixa", "dinheiro", "investimento", "aplicação", 
               "conta corrente", "conta poupança", "cc", "cp", "cdb", "lci", "lca"]
    
    possiveis = []
    for conta in contas_count.keys():
        conta_lower = conta.lower()
        if any(kw in conta_lower for kw in keywords):
            # Mas excluir se for despesa/custo
            if not any(exclude in conta_lower for exclude in ["despesa", "custo", "tarifa", "taxa", "juros"]):
                possiveis.append(conta)
    
    if possiveis:
        for conta in possiveis:
            print(f"  • {conta}")
    else:
        print("  (nenhuma conta com palavras-chave de disponibilidade encontrada)")
    
    print()

if __name__ == "__main__":
    main()



