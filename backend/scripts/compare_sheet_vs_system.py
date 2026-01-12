#!/usr/bin/env python3
"""
Script de Comparação Detalhada: Planilha vs Sistema

Compara os dados da planilha Excel com os dados do sistema de forma detalhada,
mostrando discrepâncias por mês, tipo de transação, conta, etc.

USO:
    python -m scripts.compare_sheet_vs_system
"""

import sys
import os
import argparse
import json
import tempfile
import re
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

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

# Configurações
BACKEND_URL = os.getenv("BACKEND_URL", "https://finaflow-backend-staging-556803510516.us-central1.run.app")
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ/edit?gid=1158090564#gid=1158090564"
TENANT_ID = "ed987f9e-8a32-440e-a7fc-ffeb56368d7c"
BU_ID = "b365bbaa-7796-47a8-a8e3-a0812c694c85"
QA_EMAIL = "qa@finaflow.test"
QA_PASSWORD = "QaFinaflow123!"

def download_spreadsheet(url: str) -> str:
    """Baixa a planilha do Google Sheets e retorna o caminho do arquivo temporário"""
    print("📥 Baixando planilha do Google Sheets...")
    
    # Converter URL do Google Sheets para formato de download
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', url)
    if match:
        sheet_id = match.group(1)
        excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    else:
        excel_url = url.replace('/edit', '/export?format=xlsx').split('#')[0]
    
    response = requests.get(excel_url, timeout=60)
    response.raise_for_status()
    
    # Salvar em arquivo temporário
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    tmp_file.write(response.content)
    tmp_file.close()
    
    print(f"✅ Planilha baixada: {len(response.content)} bytes")
    return tmp_file.name

def read_excel_sheets(excel_path: str) -> Dict[str, pd.DataFrame]:
    """Lê todas as abas relevantes da planilha"""
    print("\n📖 Lendo planilha Excel...")
    
    excel = pd.ExcelFile(excel_path)
    sheets = {}
    
    # Abas esperadas
    sheet_names = {
        "Plano de contas": "plano_contas",
        "Lançamento Diário": "lancamentos_diarios",
        "Lançamento Diario": "lancamentos_diarios",  # Variação
        "Lançamentos Previstos": "lancamentos_previstos"
    }
    
    for sheet_name in excel.sheet_names:
        for expected_name, key in sheet_names.items():
            if expected_name.lower() in sheet_name.lower():
                print(f"   ✅ Encontrada aba: {sheet_name} → {key}")
                df = pd.read_excel(excel, sheet_name)
                sheets[key] = df
                print(f"      Linhas: {len(df)}")
                break
    
    return sheets

def fetch_all_diarios(backend_url: str, token: str) -> List[Dict]:
    """Busca TODOS os lançamentos diários do sistema (com paginação)"""
    print("\n🔍 Buscando lançamentos diários do sistema...")
    
    all_diarios = []
    page = 1
    per_page = 100  # Limite máximo do endpoint
    
    while True:
        response = requests.get(
            f"{backend_url}/api/v1/lancamentos-diarios",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": page, "per_page": per_page}
        )
        
        if response.status_code != 200:
            print(f"❌ Erro ao buscar lançamentos diários: {response.status_code}")
            print(response.text[:500])
            break
        
        data = response.json()
        lancamentos = data.get("lancamentos", [])
        total = data.get("total", 0)
        total_pages = data.get("total_pages", 1)
        
        all_diarios.extend(lancamentos)
        print(f"   Página {page}/{total_pages}: {len(lancamentos)} lançamentos (total: {len(all_diarios)}/{total})")
        
        if page >= total_pages or len(lancamentos) == 0:
            break
        
        page += 1
    
    print(f"✅ Total de lançamentos diários no sistema: {len(all_diarios)}")
    return all_diarios

def fetch_all_previstos(backend_url: str, token: str) -> List[Dict]:
    """Busca TODOS os lançamentos previstos do sistema"""
    print("\n🔍 Buscando lançamentos previstos do sistema...")
    
    # O endpoint de previstos usa skip/limit, não paginação
    all_previstos = []
    skip = 0
    limit = 10000
    
    while True:
        response = requests.get(
            f"{backend_url}/api/v1/lancamentos-previstos",
            headers={"Authorization": f"Bearer {token}"},
            params={"skip": skip, "limit": limit}
        )
        
        if response.status_code != 200:
            print(f"❌ Erro ao buscar lançamentos previstos: {response.status_code}")
            print(response.text[:500])
            break
        
        data = response.json()
        previsoes = data.get("previsoes", [])
        total = data.get("total", 0)
        
        all_previstos.extend(previsoes)
        print(f"   Skip {skip}: {len(previsoes)} previsões (total: {len(all_previstos)}/{total})")
        
        if len(previsoes) == 0 or len(all_previstos) >= total:
            break
        
        skip += limit
    
    print(f"✅ Total de lançamentos previstos no sistema: {len(all_previstos)}")
    return all_previstos

def analyze_diarios(excel_df: pd.DataFrame, system_data: List[Dict]) -> Dict:
    """Analisa e compara lançamentos diários"""
    print("\n" + "="*80)
    print("📊 ANÁLISE: LANÇAMENTOS DIÁRIOS")
    print("="*80)
    
    # Análise da planilha
    excel_count = len(excel_df)
    print(f"\n📋 PLANILHA:")
    print(f"   Total de linhas: {excel_count}")
    
    if 'Data Movimentação' in excel_df.columns:
        excel_df['Data Movimentação'] = pd.to_datetime(excel_df['Data Movimentação'], errors='coerce')
        excel_df['Ano'] = excel_df['Data Movimentação'].dt.year
        excel_df['Mês'] = excel_df['Data Movimentação'].dt.month
        
        print(f"   Período: {excel_df['Ano'].min():.0f}-{excel_df['Ano'].max():.0f}")
        print(f"   Meses: {excel_df['Mês'].min():.0f} a {excel_df['Mês'].max():.0f}")
        
        # Contar por ano
        if 2025 in excel_df['Ano'].values:
            count_2025 = len(excel_df[excel_df['Ano'] == 2025])
            print(f"   Lançamentos 2025: {count_2025}")
    
    # Análise do sistema
    system_count = len(system_data)
    print(f"\n💻 SISTEMA:")
    print(f"   Total de lançamentos: {system_count}")
    
    # Agrupar por data
    system_by_date = defaultdict(int)
    system_by_month = defaultdict(int)
    
    for lanc in system_data:
        data_str = lanc.get('data_movimentacao', '')
        if data_str:
            try:
                dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                system_by_date[dt.date()] += 1
                system_by_month[(dt.year, dt.month)] += 1
            except:
                pass
    
    if system_by_month:
        min_month = min(system_by_month.keys())
        max_month = max(system_by_month.keys())
        print(f"   Período: {min_month[0]}-{max_month[0]}")
        print(f"   Meses: {min_month[1]} a {max_month[1]}")
        
        if (2025, 1) in system_by_month:
            count_2025 = sum(v for (y, m), v in system_by_month.items() if y == 2025)
            print(f"   Lançamentos 2025: {count_2025}")
    
    # Comparação
    print(f"\n📊 COMPARAÇÃO:")
    print(f"   Planilha: {excel_count} linhas")
    print(f"   Sistema: {system_count} lançamentos")
    print(f"   Diferença: {excel_count - system_count}")
    
    if excel_count != system_count:
        print(f"\n   ⚠️  DISCREPÂNCIA ENCONTRADA!")
        if excel_count > system_count:
            print(f"   ❌ Faltam {excel_count - system_count} lançamentos no sistema")
        else:
            print(f"   ⚠️  Sistema tem {system_count - excel_count} lançamentos a mais que a planilha")
    
    return {
        "excel_count": excel_count,
        "system_count": system_count,
        "difference": excel_count - system_count,
        "system_by_month": dict(system_by_month)
    }

def analyze_previstos(excel_df: pd.DataFrame, system_data: List[Dict]) -> Dict:
    """Analisa e compara lançamentos previstos"""
    print("\n" + "="*80)
    print("📊 ANÁLISE: LANÇAMENTOS PREVISTOS")
    print("="*80)
    
    # Análise da planilha
    excel_count = len(excel_df)
    print(f"\n📋 PLANILHA:")
    print(f"   Total de linhas: {excel_count}")
    
    if 'Mês' in excel_df.columns:
        meses = excel_df['Mês'].unique()
        print(f"   Meses únicos: {sorted(meses)}")
        print(f"   Total de meses: {len(meses)}")
    
    # Análise do sistema
    system_count = len(system_data)
    print(f"\n💻 SISTEMA:")
    print(f"   Total de previsões: {system_count}")
    
    # Agrupar por data
    system_by_month = defaultdict(int)
    
    for prev in system_data:
        data_str = prev.get('data_prevista', '')
        if data_str:
            try:
                dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                system_by_month[(dt.year, dt.month)] += 1
            except:
                pass
    
    if system_by_month:
        min_month = min(system_by_month.keys())
        max_month = max(system_by_month.keys())
        print(f"   Período: {min_month[0]}-{max_month[0]}")
        print(f"   Meses: {min_month[1]} a {max_month[1]}")
        
        if (2025, 1) in system_by_month:
            count_2025 = sum(v for (y, m), v in system_by_month.items() if y == 2025)
            print(f"   Previsões 2025: {count_2025}")
    
    # Comparação
    print(f"\n📊 COMPARAÇÃO:")
    print(f"   Planilha: {excel_count} linhas")
    print(f"   Sistema: {system_count} previsões")
    print(f"   Diferença: {excel_count - system_count}")
    
    if excel_count != system_count:
        print(f"\n   ⚠️  DISCREPÂNCIA ENCONTRADA!")
        if excel_count > system_count:
            print(f"   ❌ Faltam {excel_count - system_count} previsões no sistema")
        else:
            print(f"   ⚠️  Sistema tem {system_count - excel_count} previsões a mais que a planilha")
    
    return {
        "excel_count": excel_count,
        "system_count": system_count,
        "difference": excel_count - system_count,
        "system_by_month": dict(system_by_month)
    }

def compare_by_month(excel_df: pd.DataFrame, system_data: List[Dict], tipo: str) -> Dict:
    """Compara dados por mês"""
    print(f"\n📅 COMPARAÇÃO POR MÊS ({tipo}):")
    print("-" * 80)
    
    # Agrupar planilha por mês
    excel_by_month = defaultdict(int)
    if tipo == "diarios" and 'Data Movimentação' in excel_df.columns:
        excel_df['Data Movimentação'] = pd.to_datetime(excel_df['Data Movimentação'], errors='coerce')
        excel_df['Ano'] = excel_df['Data Movimentação'].dt.year
        excel_df['Mês'] = excel_df['Data Movimentação'].dt.month
        for _, row in excel_df.iterrows():
            if pd.notna(row.get('Ano')) and pd.notna(row.get('Mês')):
                excel_by_month[(int(row['Ano']), int(row['Mês']))] += 1
    elif tipo == "previstos":
        # Tentar diferentes colunas de data
        if 'Data Prevista' in excel_df.columns:
            excel_df['Data Prevista'] = pd.to_datetime(excel_df['Data Prevista'], errors='coerce')
            excel_df['Ano'] = excel_df['Data Prevista'].dt.year
            excel_df['Mês'] = excel_df['Data Prevista'].dt.month
            for _, row in excel_df.iterrows():
                if pd.notna(row.get('Ano')) and pd.notna(row.get('Mês')):
                    excel_by_month[(int(row['Ano']), int(row['Mês']))] += 1
        elif 'Mês' in excel_df.columns:
            for _, row in excel_df.iterrows():
                mes = row.get('Mês')
                if pd.notna(mes):
                    # Se for Timestamp, extrair mês
                    if isinstance(mes, pd.Timestamp):
                        excel_by_month[(mes.year, mes.month)] += 1
                    elif isinstance(mes, (int, float)):
                        excel_by_month[(2025, int(mes))] += 1
                    elif isinstance(mes, str):
                        try:
                            dt = pd.to_datetime(mes, errors='coerce')
                            if pd.notna(dt):
                                excel_by_month[(dt.year, dt.month)] += 1
                        except:
                            pass
    
    # Agrupar sistema por mês
    system_by_month = defaultdict(int)
    date_field = 'data_movimentacao' if tipo == "diarios" else 'data_prevista'
    
    for item in system_data:
        data_str = item.get(date_field, '')
        if data_str:
            try:
                dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                system_by_month[(dt.year, dt.month)] += 1
            except:
                pass
    
    # Comparar
    all_months = set(list(excel_by_month.keys()) + list(system_by_month.keys()))
    discrepancies = []
    
    print(f"{'Mês':<10} {'Planilha':<12} {'Sistema':<12} {'Diferença':<12} {'Status':<10}")
    print("-" * 80)
    
    for month in sorted(all_months):
        excel_count = excel_by_month.get(month, 0)
        system_count = system_by_month.get(month, 0)
        diff = excel_count - system_count
        
        status = "✅" if diff == 0 else "❌"
        if diff != 0:
            discrepancies.append({
                "month": month,
                "excel": excel_count,
                "system": system_count,
                "difference": diff
            })
        
        print(f"{f'{month[0]}-{month[1]:02d}':<10} {excel_count:<12} {system_count:<12} {diff:<12} {status:<10}")
    
    return {
        "discrepancies": discrepancies,
        "excel_by_month": dict(excel_by_month),
        "system_by_month": dict(system_by_month)
    }

def main():
    print("="*80)
    print("🔍 COMPARAÇÃO DETALHADA: PLANILHA vs SISTEMA")
    print("="*80)
    
    # 1. Login
    print("\n🔐 Fazendo login...")
    login_response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"username={QA_EMAIL}&password={QA_PASSWORD}",
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        print(login_response.text)
        sys.exit(1)
    
    token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Selecionar Business Unit
    print("\n🏢 Selecionando Business Unit...")
    select_response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/select-business-unit",
        headers=headers,
        json={"business_unit_id": BU_ID},
        timeout=10
    )
    
    if select_response.status_code != 200:
        print(f"❌ Erro ao selecionar BU: {select_response.status_code}")
        sys.exit(1)
    
    bu_token = select_response.json()['access_token']
    bu_headers = {"Authorization": f"Bearer {bu_token}"}
    
    # 3. Baixar e ler planilha
    excel_path = download_spreadsheet(SPREADSHEET_URL)
    try:
        sheets = read_excel_sheets(excel_path)
        
        # 4. Buscar dados do sistema
        diarios_system = fetch_all_diarios(BACKEND_URL, bu_token)
        previstos_system = fetch_all_previstos(BACKEND_URL, bu_token)
        
        # 5. Análises
        results = {}
        
        if "lancamentos_diarios" in sheets:
            results["diarios"] = analyze_diarios(sheets["lancamentos_diarios"], diarios_system)
            results["diarios_by_month"] = compare_by_month(
                sheets["lancamentos_diarios"],
                diarios_system,
                "diarios"
            )
        
        if "lancamentos_previstos" in sheets:
            results["previstos"] = analyze_previstos(sheets["lancamentos_previstos"], previstos_system)
            results["previstos_by_month"] = compare_by_month(
                sheets["lancamentos_previstos"],
                previstos_system,
                "previstos"
            )
        
        # 6. Resumo final
        print("\n" + "="*80)
        print("📋 RESUMO FINAL")
        print("="*80)
        
        if "diarios" in results:
            diarios = results["diarios"]
            print(f"\n📊 Lançamentos Diários:")
            print(f"   Planilha: {diarios['excel_count']}")
            print(f"   Sistema: {diarios['system_count']}")
            print(f"   Diferença: {diarios['difference']}")
            if diarios['difference'] != 0:
                print(f"   ⚠️  PROBLEMA: {abs(diarios['difference'])} lançamentos {'faltando' if diarios['difference'] > 0 else 'extras'} no sistema")
        
        if "previstos" in results:
            previstos = results["previstos"]
            print(f"\n📊 Lançamentos Previstos:")
            print(f"   Planilha: {previstos['excel_count']}")
            print(f"   Sistema: {previstos['system_count']}")
            print(f"   Diferença: {previstos['difference']}")
            if previstos['difference'] != 0:
                print(f"   ⚠️  PROBLEMA: {abs(previstos['difference'])} previsões {'faltando' if previstos['difference'] > 0 else 'extras'} no sistema")
        
        # Salvar resultados em JSON (convertendo tuplas para strings)
        output_file = backend_path / "artifacts" / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Converter tuplas em strings para JSON
        def convert_for_json(obj):
            if isinstance(obj, dict):
                return {str(k): convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_for_json(item) for item in obj]
            elif isinstance(obj, tuple):
                return str(obj)
            else:
                return obj
        
        results_json = convert_for_json(results)
        
        with open(output_file, 'w') as f:
            json.dump(results_json, f, indent=2, default=str)
        
        print(f"\n💾 Resultados salvos em: {output_file}")
        
    finally:
        # Limpar arquivo temporário
        os.unlink(excel_path)

if __name__ == "__main__":
    main()

