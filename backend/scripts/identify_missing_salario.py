#!/usr/bin/env python3
"""
Script para identificar exatamente quais linhas de Salário não estão sendo seedadas e por quê.
"""

import pandas as pd
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import requests
import os

BACKEND_URL = os.getenv('BACKEND_URL', 'https://finaflow-backend-staging-642830139828.us-central1.run.app')
QA_USERNAME = os.getenv('QA_USERNAME', 'qa@finaflow.test')
QA_PASSWORD = os.getenv('QA_PASSWORD', 'QaFinaflow123!')

def parse_date(date_value):
    if pd.isna(date_value):
        return None
    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, pd.Timestamp):
        return date_value.to_pydatetime()
    return None

def parse_currency(value):
    if pd.isna(value) or value == '' or value is None:
        return Decimal('0')
    s = str(value).strip()
    s = s.replace('R$', '').replace('$', '').replace(' ', '')
    if s == '':
        return Decimal('0')
    has_dot = '.' in s
    has_comma = ',' in s
    try:
        if has_dot and has_comma:
            s_clean = s.replace('.', '').replace(',', '.')
        elif has_comma:
            s_clean = s.replace(',', '.')
        else:
            s_clean = s
        return Decimal(s_clean)
    except:
        return Decimal('0')

def main():
    print('=== IDENTIFICAR: Linhas de Salário não seedadas ===\n')
    
    # 1. Ler planilha
    excel_file = Path('data/fluxo_caixa_2025.xlsx')
    df = pd.read_excel(excel_file, sheet_name='Lançamento Diário')
    
    # Filtrar apenas 'Salário' em 'Custos com Mão de Obra'
    salario_df = df[
        (df['Grupo'].str.contains('Custo', case=False, na=False)) &
        (df['Subgrupo'].str.contains('Mão de Obra', case=False, na=False)) &
        (df['Conta'].str.contains('Salário', case=False, na=False))
    ]
    
    print(f'Total de lançamentos de Salário na planilha: {len(salario_df)}\n')
    
    # 2. Login na API
    login_resp = requests.post(f'{BACKEND_URL}/api/v1/auth/login', json={'username': QA_USERNAME, 'password': QA_PASSWORD})
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 3. Buscar todos os lançamentos do sistema
    print('Buscando lançamentos do sistema...')
    sistema_por_linha = {}  # linha -> item
    
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
        
        for item in all_items:
            subgrupo = item.get('subgroup', '')
            conta = item.get('account', '')
            if 'mão de obra' in subgrupo.lower() and ('salário' in conta.lower() or 'salario' in conta.lower()):
                obs = item.get('description', '') or item.get('observacoes', '') or ''
                # Extrair número da linha da observação
                if 'linha' in obs.lower():
                    try:
                        linha_num = int(obs.split('linha')[1].strip().split()[0])
                        sistema_por_linha[linha_num] = item
                    except:
                        pass
    
    print(f'Total de lançamentos de Salário no sistema: {len(sistema_por_linha)}\n')
    
    # 4. Comparar linha a linha
    print('Comparando linha a linha...\n')
    
    faltantes = []
    problemas = {
        'sem_data': [],
        'data_fora_2025': [],
        'sem_valor': [],
        'valor_zero': [],
        'sem_grupo': [],
        'sem_subgrupo': [],
        'sem_conta': [],
        'nao_encontrado_no_sistema': []
    }
    
    for idx, row in salario_df.iterrows():
        row_num = idx + 2
        
        # Parsear data
        data_raw = row['Data Movimentação']
        data_obj = parse_date(data_raw)
        
        if not data_obj:
            problemas['sem_data'].append(row_num)
            continue
        
        if data_obj.year != 2025:
            problemas['data_fora_2025'].append(row_num)
            continue
        
        # Parsear valor
        valor_str = str(row['Valor']) if pd.notna(row['Valor']) else '0'
        valor = parse_currency(valor_str)
        
        if valor <= 0:
            problemas['valor_zero'].append(row_num)
            continue
        
        # Verificar grupo/subgrupo/conta
        grupo = str(row['Grupo']) if pd.notna(row['Grupo']) else ''
        subgrupo = str(row['Subgrupo']) if pd.notna(row['Subgrupo']) else ''
        conta = str(row['Conta']) if pd.notna(row['Conta']) else ''
        
        if not grupo or grupo == 'nan':
            problemas['sem_grupo'].append(row_num)
            continue
        
        if not subgrupo or subgrupo == 'nan':
            problemas['sem_subgrupo'].append(row_num)
            continue
        
        if not conta or conta == 'nan':
            problemas['sem_conta'].append(row_num)
            continue
        
        # Verificar se está no sistema
        if row_num not in sistema_por_linha:
            problemas['nao_encontrado_no_sistema'].append({
                'row': row_num,
                'date': data_obj.date(),
                'valor': valor,
                'grupo': grupo,
                'subgrupo': subgrupo,
                'conta': conta,
                'observacoes': str(row['Observações']) if pd.notna(row['Observações']) else ''
            })
    
    # 5. Relatório
    print('=== ANÁLISE DE PROBLEMAS ===\n')
    for problema, items in sorted(problemas.items(), key=lambda x: len(x[1]) if isinstance(x[1], list) else 0, reverse=True):
        if len(items) > 0:
            print(f'{problema:30} {len(items):4} lançamentos')
            if problema == 'nao_encontrado_no_sistema':
                print('  Primeiros 20 exemplos:')
                for item in items[:20]:
                    obs_str = item['observacoes'][:30] if item['observacoes'] else '(sem obs)'
                    row = item['row']
                    date = item['date']
                    valor = item['valor']
                    grupo = item['grupo'][:20]
                    subgrupo = item['subgrupo'][:30]
                    conta = item['conta'][:20]
                    print(f'    Linha {row:4d} | {date} | R$ {float(valor):>10,.2f} | Grupo: {grupo} | Subgrupo: {subgrupo} | Conta: {conta} | Obs: "{obs_str}"')
            elif len(items) <= 10:
                print(f'  Linhas: {items[:10]}')
    
    print(f'\n=== RESUMO ===\n')
    total_problemas = sum(len(v) if isinstance(v, list) else 0 for v in problemas.values())
    print(f'Total de lançamentos na planilha: {len(salario_df)}')
    print(f'Total de lançamentos no sistema: {len(sistema_por_linha)}')
    print(f'Total com problemas: {total_problemas}')
    nao_encontrados = problemas['nao_encontrado_no_sistema']
    print(f'Lançamentos não encontrados no sistema: {len(nao_encontrados)}')

if __name__ == '__main__':
    main()

