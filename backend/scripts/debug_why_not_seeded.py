#!/usr/bin/env python3
"""
Script para identificar exatamente quais lançamentos não estão sendo seedados e por quê.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from decimal import Decimal
from collections import defaultdict
from datetime import datetime
import requests

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

def parse_date(date_value):
    """Converte valor para datetime"""
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return None
    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, pd.Timestamp):
        return date_value.to_pydatetime()
    return None

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

BACKEND_URL = os.getenv('BACKEND_URL', 'https://finaflow-backend-staging-642830139828.us-central1.run.app')
QA_USERNAME = os.getenv('QA_USERNAME', 'qa@finaflow.test')
QA_PASSWORD = os.getenv('QA_PASSWORD', 'QaFinaflow123!')

def main():
    print('=== INVESTIGAÇÃO: Por que 55 lançamentos de Salário não foram seedados? ===\n')
    
    # 1. Ler planilha
    excel_file = backend_path / 'data' / 'fluxo_caixa_2025.xlsx'
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
        
        # Filtrar apenas 'Salário' em 'Custos com Mão de Obra'
        for item in all_items:
            subgrupo = item.get('subgroup', '')
            conta = item.get('account', '')
            if 'mão de obra' in subgrupo.lower() and ('salário' in conta.lower() or 'salario' in conta.lower()):
                # Criar chave: data + valor + observações (se houver)
                data_str = item.get('date', '')
                amount_str = item.get('amount', '0')
                obs = item.get('description', '') or item.get('observacoes', '') or ''
                try:
                    data_obj = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                    valor = Decimal(str(amount_str)).quantize(Decimal('0.01'))
                    # Chave com observações para diferenciar
                    chave = f"{data_obj.date()}_{valor}_{obs[:50]}"
                    sistema_lancamentos[chave] = item
                except:
                    pass
    
    print(f'Total de lançamentos de Salário no sistema: {len(sistema_lancamentos)}\n')
    
    # 4. Comparar linha a linha
    print('Comparando linha a linha...\n')
    
    faltantes = []
    por_motivo = defaultdict(list)
    
    for idx, row in salario_df.iterrows():
        row_num = idx + 2
        
        # Parsear data
        data_raw = row['Data Movimentação']
        data_obj = parse_date(data_raw)
        
        if not data_obj or data_obj.year != 2025:
            continue
        
        # Parsear valor
        valor_str = str(row['Valor']) if pd.notna(row['Valor']) else '0'
        valor = parse_currency(valor_str)
        
        if valor <= 0:
            continue
        
        # Parsear observações
        observacoes = str(row['Observações']) if pd.notna(row['Observações']) else ''
        observacoes = observacoes.strip()
        
        # Criar chaves possíveis (com e sem observações)
        valor_rounded = valor.quantize(Decimal('0.01'))
        
        # Chave com observações (se houver)
        if observacoes:
            chave_com_obs = f"{data_obj.date()}_{valor_rounded}_{observacoes[:50]}"
        else:
            # Sem observações, usar número da linha esperado
            obs_esperada = f"Lançamento linha {row_num}"
            chave_com_obs = f"{data_obj.date()}_{valor_rounded}_{obs_esperada}"
        
        # Verificar se existe no sistema
        encontrado = False
        for chave_sistema in sistema_lancamentos.keys():
            if chave_sistema.startswith(f"{data_obj.date()}_{valor_rounded}_"):
                # Verificar se observações batem
                obs_sistema = chave_sistema.split('_', 2)[2] if '_' in chave_sistema[20:] else ''
                if observacoes:
                    if observacoes[:50] in obs_sistema:
                        encontrado = True
                        break
                else:
                    # Sem observações, verificar se tem número da linha
                    if f"linha {row_num}" in obs_sistema.lower():
                        encontrado = True
                        break
        
        if not encontrado:
            faltantes.append({
                'row': row_num,
                'date': data_obj.date(),
                'valor': valor,
                'observacoes': observacoes,
                'conta': str(row['Conta']) if pd.notna(row['Conta']) else '',
            })
            
            # Classificar por motivo provável
            if not observacoes:
                por_motivo['sem_observacoes'].append(row_num)
            else:
                por_motivo['com_observacoes'].append(row_num)
    
    # 5. Relatório
    print(f'❌ Lançamentos faltantes: {len(faltantes)}\n')
    
    if len(faltantes) > 0:
        print('Análise por motivo:\n')
        for motivo, items in sorted(por_motivo.items(), key=lambda x: len(x[1]), reverse=True):
            print(f'{motivo:20} {len(items):4} lançamentos')
        
        print(f'\nPrimeiros 30 lançamentos faltantes:')
        for item in faltantes[:30]:
            obs_str = item['observacoes'][:30] if item['observacoes'] else '(sem obs)'
            row = item['row']
            date = item['date']
            valor = item['valor']
            print(f'  Linha {row:4d} | {date} | R$ {float(valor):>10,.2f} | "{obs_str}"')
        
        if len(faltantes) > 30:
            print(f'  ... e mais {len(faltantes) - 30} lançamentos')
        
        # Agrupar por data+valor para verificar duplicatas
        print(f'\n=== VERIFICAR: Duplicatas na planilha ===\n')
        por_chave = defaultdict(list)
        for item in faltantes:
            date = item['date']
            valor = item['valor']
            chave = f'{date}_{valor.quantize(Decimal("0.01"))}'
            por_chave[chave].append(item)
        
        duplicatas = {k: v for k, v in por_chave.items() if len(v) > 1}
        if duplicatas:
            print(f'Chaves duplicadas (mesma data + valor): {len(duplicatas)}\n')
            for chave, items in list(duplicatas.items())[:10]:
                data, valor = chave.split('_')
                print(f'  {data} | R$ {float(Decimal(valor)):,.2f}: {len(items)} lançamentos')
                for item in items[:3]:
                    obs_str = item['observacoes'][:30] if item['observacoes'] else '(sem obs)'
                    row = item['row']
                    print(f'    Linha {row}: "{obs_str}"')
    else:
        print('✅ Todos os lançamentos foram seedados!')

if __name__ == '__main__':
    main()

