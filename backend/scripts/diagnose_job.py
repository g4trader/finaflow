#!/usr/bin/env python3
"""
Script de diagnóstico para Cloud Run Jobs
Verifica estrutura de diretórios e arquivos
"""

import os
import sys
from pathlib import Path

print("=" * 80)
print("DIAGNÓSTICO DO CONTAINER")
print("=" * 80)
print()

# Verificar diretório atual
print(f"📁 Diretório atual: {os.getcwd()}")
print()

# Verificar PYTHONPATH
print(f"🐍 PYTHONPATH: {os.getenv('PYTHONPATH', 'não definido')}")
print()

# Verificar estrutura de diretórios
print("📂 Estrutura de diretórios:")
for path in ["/app", "/app/data", "/app/scripts", "."]:
    p = Path(path)
    if p.exists():
        print(f"   ✅ {path} existe")
        if p.is_dir():
            try:
                files = list(p.iterdir())[:10]
                print(f"      Arquivos (primeiros 10): {[f.name for f in files]}")
            except:
                print(f"      (não foi possível listar)")
    else:
        print(f"   ❌ {path} não existe")
print()

# Verificar arquivo Excel
excel_paths = [
    "data/fluxo_caixa_2025.xlsx",
    "/app/data/fluxo_caixa_2025.xlsx",
    "./data/fluxo_caixa_2025.xlsx",
]

print("📊 Verificando arquivo Excel:")
for excel_path in excel_paths:
    p = Path(excel_path)
    if p.exists():
        print(f"   ✅ {excel_path} existe ({p.stat().st_size} bytes)")
    else:
        print(f"   ❌ {excel_path} não existe")
print()

# Verificar scripts
script_paths = [
    "scripts/seed_from_client_sheet.py",
    "scripts/validate_dashboard_against_client_sheet.py",
    "/app/scripts/seed_from_client_sheet.py",
]

print("🔧 Verificando scripts:")
for script_path in script_paths:
    p = Path(script_path)
    if p.exists():
        print(f"   ✅ {script_path} existe")
    else:
        print(f"   ❌ {script_path} não existe")
print()

# Tentar importar módulos
print("📦 Tentando importar módulos:")
try:
    import scripts.seed_from_client_sheet
    print("   ✅ scripts.seed_from_client_sheet importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro ao importar scripts.seed_from_client_sheet: {e}")

try:
    import scripts.validate_dashboard_against_client_sheet
    print("   ✅ scripts.validate_dashboard_against_client_sheet importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro ao importar scripts.validate_dashboard_against_client_sheet: {e}")

print()
print("=" * 80)

