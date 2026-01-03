#!/usr/bin/env python3
"""Verifica todas as abas do Excel para encontrar onde estão as disponibilidades"""

import sys
from pathlib import Path
import pandas as pd

backend_path = Path(__file__).parent.parent
EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"

def main():
    print("="*80)
    print("📊 ABAS DO EXCEL")
    print("="*80)
    
    xls = pd.ExcelFile(EXCEL_FILE)
    print(f"\nTotal de abas: {len(xls.sheet_names)}\n")
    
    for sheet_name in xls.sheet_names:
        print(f"📄 {sheet_name}")
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, nrows=5)
            print(f"   Colunas: {list(df.columns)[:10]}...")
            print(f"   Linhas (primeiras 5):")
            for idx, row in df.head(3).iterrows():
                print(f"     {row.to_dict()}")
        except Exception as e:
            print(f"   Erro ao ler: {e}")
        print()

if __name__ == "__main__":
    main()



