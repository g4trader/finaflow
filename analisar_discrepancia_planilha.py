#!/usr/bin/env python3
"""
🔍 ANÁLISE DE DISCREPÂNCIA ENTRE PLANILHA E SISTEMA
Comparar dados da planilha "Lançamento Diário" com o sistema
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
from datetime import datetime

# Configurações
SPREADSHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
SHEET_NAME = "Lançamento Diário"
CREDENTIALS_FILE = "google_credentials.json"

def conectar_google_sheets():
    """Conectar ao Google Sheets API"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        print(f"❌ Erro ao conectar Google Sheets: {e}")
        return None

def analisar_planilha():
    """Analisar dados da planilha"""
    print("📊 ANALISANDO PLANILHA GOOGLE SHEETS...")
    
    service = conectar_google_sheets()
    if not service:
        return None
    
    try:
        # Buscar dados da planilha
        range_name = f"{SHEET_NAME}!A:Z"
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        print(f"📊 Total de linhas na planilha: {len(values)}")
        
        if not values:
            print("❌ Nenhum dado encontrado na planilha")
            return None
        
        # Analisar cabeçalhos
        headers = values[0] if values else []
        print(f"📊 Cabeçalhos: {headers}")
        
        # Contar registros de dados (excluindo cabeçalho)
        data_rows = values[1:] if len(values) > 1 else []
        print(f"📊 Registros de dados na planilha: {len(data_rows)}")
        
        # Analisar algumas linhas
        print(f"📊 Primeiras 5 linhas de dados:")
        for i, row in enumerate(data_rows[:5]):
            print(f"  Linha {i+2}: {row}")
        
        # Verificar se há linhas vazias
        empty_rows = sum(1 for row in data_rows if not any(cell.strip() for cell in row))
        print(f"📊 Linhas vazias: {empty_rows}")
        
        # Contar registros válidos
        valid_rows = sum(1 for row in data_rows if any(cell.strip() for cell in row))
        print(f"📊 Registros válidos na planilha: {valid_rows}")
        
        return {
            'total_rows': len(values),
            'data_rows': len(data_rows),
            'valid_rows': valid_rows,
            'empty_rows': empty_rows,
            'headers': headers,
            'sample_data': data_rows[:10]
        }
        
    except Exception as e:
        print(f"❌ Erro ao analisar planilha: {e}")
        return None

def analisar_sistema():
    """Analisar dados do sistema via API"""
    print("\n📊 ANALISANDO SISTEMA...")
    
    try:
        # Fazer login
        login_data = {
            'username': 'lucianoterres',
            'password': 'K8RBlmLZn16h'
        }
        
        response = requests.post('https://finaflow-backend-642830139828.us-central1.run.app/api/v1/auth/login', 
                               data=login_data)
        
        if response.status_code != 200:
            print(f"❌ Erro no login: {response.status_code} - {response.text}")
            return None
        
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Buscar lançamentos
        lancamentos_response = requests.get('https://finaflow-backend-642830139828.us-central1.run.app/api/v1/lancamentos-diarios?limit=1', headers=headers)
        
        if lancamentos_response.status_code != 200:
            print(f"❌ Erro ao buscar lançamentos: {lancamentos_response.status_code} - {lancamentos_response.text}")
            return None
        
        data = lancamentos_response.json()
        total = data.get('total', 0)
        print(f"📊 Total de lançamentos no sistema: {total}")
        
        # Buscar alguns registros para análise
        lancamentos_response = requests.get('https://finaflow-backend-642830139828.us-central1.run.app/api/v1/lancamentos-diarios?limit=10', headers=headers)
        
        if lancamentos_response.status_code == 200:
            data = lancamentos_response.json()
            lancamentos = data.get('lancamentos', [])
            print(f"📊 Primeiros 5 registros do sistema:")
            for i, lanc in enumerate(lancamentos[:5]):
                print(f"  {i+1}. Data: {lanc.get('data_movimentacao')}, Valor: {lanc.get('valor')}, Conta: {lanc.get('conta', {}).get('name', 'N/A')}")
        
        return {
            'total': total,
            'sample_data': lancamentos[:10]
        }
        
    except Exception as e:
        print(f"❌ Erro ao analisar sistema: {e}")
        return None

def comparar_dados(planilha_data, sistema_data):
    """Comparar dados da planilha com o sistema"""
    print("\n🔍 COMPARANDO DADOS...")
    
    if not planilha_data or not sistema_data:
        print("❌ Dados insuficientes para comparação")
        return
    
    planilha_total = planilha_data['valid_rows']
    sistema_total = sistema_data['total']
    
    diferenca = planilha_total - sistema_total
    
    print(f"📊 PLANILHA: {planilha_total} registros válidos")
    print(f"📊 SISTEMA: {sistema_total} registros")
    print(f"📊 DIFERENÇA: {diferenca} registros")
    
    if diferenca > 0:
        print(f"⚠️  O sistema tem {diferenca} registros a menos que a planilha")
    elif diferenca < 0:
        print(f"⚠️  O sistema tem {abs(diferenca)} registros a mais que a planilha")
    else:
        print("✅ Números coincidem!")
    
    # Análise detalhada
    print(f"\n📊 ANÁLISE DETALHADA:")
    print(f"  - Planilha total de linhas: {planilha_data['total_rows']}")
    print(f"  - Planilha linhas de dados: {planilha_data['data_rows']}")
    print(f"  - Planilha linhas vazias: {planilha_data['empty_rows']}")
    print(f"  - Planilha registros válidos: {planilha_data['valid_rows']}")
    print(f"  - Sistema registros: {sistema_data['total']}")

def main():
    """Função principal"""
    print("🔍 ANÁLISE DE DISCREPÂNCIA ENTRE PLANILHA E SISTEMA")
    print("=" * 60)
    
    # Analisar planilha
    planilha_data = analisar_planilha()
    
    # Analisar sistema
    sistema_data = analisar_sistema()
    
    # Comparar dados
    comparar_dados(planilha_data, sistema_data)
    
    print("\n" + "=" * 60)
    print("✅ Análise concluída!")

if __name__ == "__main__":
    main()
