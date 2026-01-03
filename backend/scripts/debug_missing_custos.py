#!/usr/bin/env python3
"""
Script para identificar lançamentos de Custos com Mão de Obra que não foram seedados.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from decimal import Decimal
from collections import defaultdict
import requests
from datetime import datetime

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

def parse_currency(value):
    """Converte valor monetário (BRL) para Decimal"""
    if pd.isna(value) or value == "" or value is None:
        return Decimal("0")
    s = str(value).strip()
    s = s.replace("R$", "").replace("$", "").replace(" ", "")
    if s == "":
        return Decimal("0")
    has_dot = "." in s
    has_comma = "," in s
    try:
        if has_dot and has_comma:
            s_clean = s.replace(".", "").replace(",", ".")
        elif has_comma:
            s_clean = s.replace(",", ".")
        else:
            s_clean = s
        return Decimal(s_clean)
    except Exception:
        return Decimal("0")

def parse_date(date_value):
    """Converte valor para datetime"""
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return None
    date_str = str(date_value).strip()
    if not date_str or date_str.lower() == 'nan':
        return None
    formats = [
        "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d",
        "%d/%m/%y", "%y-%m-%d", "%d-%m-%y", "%y/%m/%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return None

BACKEND_URL = os.getenv('BACKEND_URL', 'https://finaflow-backend-staging-642830139828.us-central1.run.app')
QA_USERNAME = os.getenv('QA_USERNAME', 'qa@finaflow.test')
QA_PASSWORD = os.getenv('QA_PASSWORD', 'QaFinaflow123!')

def main():
    print('=== IDENTIFICAR LANÇAMENTOS FALTANTES: Custos com Mão de Obra ===\n')
    
    # 1. Ler planilha
    excel_file = backend_path / 'data' / 'fluxo_caixa_2025.xlsx'
    df = pd.read_excel(excel_file, sheet_name='Lançamento Diário')
    
    # Filtrar apenas 'Custos com Mão de Obra'
    mao_obra_df = df[
        (df['Grupo'].str.contains('Custo', case=False, na=False)) &
        (df['Subgrupo'].str.contains('Mão de Obra', case=False, na=False))
    ]
    
    print(f'Total de lançamentos na planilha: {len(mao_obra_df)}\n')
    
    # 2. Login na API
    login_resp = requests.post(f'{BACKEND_URL}/api/v1/auth/login', json={'username': QA_USERNAME, 'password': QA_PASSWORD})
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 3. Buscar todos os lançamentos do sistema
    print('Buscando lançamentos do sistema...')
    sistema_lancamentos = {}
    
    for month in range(1, 13):
        all_items = []
        page = 1
        while True:
            resp = requests.get(f'{BACKEND_URL}/api/v1/financial/monthly-transactions?year=2025&month={month}&type=CUSTO&page={page}&page_size=200', headers=headers)
            if resp.status_code != 200:
                break
            data = resp.json()
            items = data.get('items', [])
            all_items.extend(items)
            if page >= data.get('total_pages', 1):
                break
            page += 1
        
        # Filtrar apenas 'Custos com Mão de Obra'
        for item in all_items:
            subgrupo = item.get('subgroup', '')
            if 'mão de obra' in subgrupo.lower() or 'mao de obra' in subgrupo.lower():
                # Criar chave: data + valor (arredondado para 2 casas)
                data_str = item.get('date', '')
                amount_str = item.get('amount', '0')
                try:
                    data_obj = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                    valor = Decimal(str(amount_str)).quantize(Decimal('0.01'))
                    chave = f"{data_obj.date()}_{valor}"
                    sistema_lancamentos[chave] = item
                except:
                    pass
    
    print(f'Total de lançamentos no sistema: {len(sistema_lancamentos)}\n')
    
    # 4. Comparar linha a linha
    print('Comparando linha a linha...\n')
    
    faltantes = []
    por_mes_faltante = defaultdict(Decimal)
    
    for idx, row in mao_obra_df.iterrows():
        # Parsear data
        data_str = str(row['Data Movimentação']) if pd.notna(row['Data Movimentação']) else ''
        data_obj = parse_date(data_str)
        
        if not data_obj or data_obj.year != 2025:
            continue
        
        # Parsear valor
        valor_str = str(row['Valor']) if pd.notna(row['Valor']) else '0'
        valor = parse_currency(valor_str)
        
        if valor <= 0:
            continue
        
        # Criar chave
        valor_rounded = valor.quantize(Decimal('0.01'))
        chave = f"{data_obj.date()}_{valor_rounded}"
        
        # Verificar se existe no sistema
        if chave not in sistema_lancamentos:
            faltantes.append({
                'row': idx + 2,  # +2 porque Excel começa em 1 e tem header
                'date': data_obj.date(),
                'valor': valor,
                'subgrupo': str(row['Subgrupo']) if pd.notna(row['Subgrupo']) else '',
                'conta': str(row['Conta']) if pd.notna(row['Conta']) else '',
            })
            por_mes_faltante[data_obj.month] += valor
    
    # 5. Relatório
    print(f'❌ Lançamentos faltantes: {len(faltantes)}\n')
    
    if len(faltantes) > 0:
        print('Totais faltantes por mês:')
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        for month in range(1, 13):
            month_name = month_names[month-1]
            total = por_mes_faltante.get(month, Decimal('0'))
            if total > 0:
                print(f'  {month_name}/2025: R$ {float(total):>12,.2f}')
        
        total_faltante = sum(por_mes_faltante.values())
        print(f'\nTotal faltante: R$ {float(total_faltante):,.2f}')
        
        # Mostrar primeiros 20 faltantes
        print(f'\nPrimeiros 20 lançamentos faltantes:')
        for item in faltantes[:20]:
            row = item['row']
            date = item['date']
            valor = item['valor']
            subgrupo = item['subgrupo'][:40]
            conta = item['conta'][:30]
            print(f'  Linha {row:4d} | {date} | R$ {float(valor):>10,.2f} | {subgrupo} | {conta}')
        
        if len(faltantes) > 20:
            print(f'  ... e mais {len(faltantes) - 20} lançamentos')
    else:
        print('✅ Todos os lançamentos foram seedados!')
        print('   A diferença pode ser devido a arredondamentos ou lançamentos duplicados.')

if __name__ == '__main__':
    main()

