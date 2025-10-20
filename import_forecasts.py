#!/usr/bin/env python3
"""
Script para importar previsões financeiras do CSV
"""

import csv
import datetime
import sys
import os

# Adicionar o diretório pai ao path para importar os modelos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import get_db, engine
from backend.app.models.chart_of_accounts import ChartAccount
from backend.app.models.auth import BusinessUnit

def parse_currency(value_str):
    """Converte string de moeda para float"""
    if not value_str or value_str.strip() == '':
        return 0.0
    
    # Remove R$, espaços e converte vírgula para ponto
    clean_value = value_str.replace('R$', '').replace(' ', '').replace(',', '.').strip()
    
    try:
        return float(clean_value)
    except ValueError:
        print(f"⚠️ Valor inválido: {value_str}")
        return 0.0

def parse_date(date_str):
    """Converte string de data para objeto date"""
    if not date_str or date_str.strip() == '':
        return None
    
    try:
        # Formato: 01/01/2025
        day, month, year = date_str.split('/')
        return datetime.datetime(int(year), int(month), int(day)).date()
    except:
        print(f"⚠️ Data inválida: {date_str}")
        return None

def import_forecasts(csv_file_path, business_unit_name="Matriz"):
    """Importa previsões do arquivo CSV"""
    
    print(f"🚀 Iniciando importação de previsões para BU: {business_unit_id}")
    print(f"📁 Arquivo: {csv_file_path}")
    
    # Verificar se o arquivo existe
    if not os.path.exists(csv_file_path):
        print(f"❌ Arquivo não encontrado: {csv_file_path}")
        return
    
    # Conectar ao banco
    db = next(get_db())
    
    try:
        # Buscar a Business Unit
        business_unit = db.query(BusinessUnit).filter(
            BusinessUnit.name.ilike(f"%{business_unit_name}%")
        ).first()
        
        if not business_unit:
            print(f"❌ Business Unit '{business_unit_name}' não encontrada")
            return
        
        print(f"✅ Business Unit encontrada: {business_unit.name} (ID: {business_unit.id})")
        
        # Ler o arquivo CSV
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Contadores
            total_rows = 0
            processed = 0
            skipped = 0
            errors = []
            
            print("\n📊 Processando linhas...")
            
            for row_num, row in enumerate(reader, start=2):
                total_rows += 1
                
                try:
                    # Validar campos obrigatórios
                    if not row.get('Ano/Mês') or not row.get('Conta') or not row.get('Valor'):
                        skipped += 1
                        continue
                    
                    # Processar data
                    forecast_date = parse_date(row['Ano/Mês'])
                    if not forecast_date:
                        skipped += 1
                        continue
                    
                    # Processar valor
                    amount = parse_currency(row['Valor'])
                    if amount == 0:
                        skipped += 1
                        continue
                    
                    # Buscar conta pelo nome
                    account_name = row['Conta'].strip()
                    chart_account = db.query(ChartAccount).filter(
                        ChartAccount.name.ilike(f"%{account_name}%"),
                        ChartAccount.is_active == True
                    ).first()
                    
                    if not chart_account:
                        skipped += 1
                        errors.append(f"Linha {row_num}: Conta '{account_name}' não encontrada")
                        continue
                    
                    print(f"  ✅ Linha {row_num}: {account_name} - R$ {amount:.2f} - {forecast_date}")
                    processed += 1
                    
                except Exception as e:
                    skipped += 1
                    errors.append(f"Linha {row_num}: Erro - {str(e)}")
                    continue
            
            print(f"\n📈 RESUMO DA IMPORTAÇÃO:")
            print(f"   Total de linhas: {total_rows}")
            print(f"   Processadas: {processed}")
            print(f"   Ignoradas: {skipped}")
            
            if errors:
                print(f"\n⚠️ ERROS ENCONTRADOS:")
                for error in errors[:10]:  # Mostrar apenas os primeiros 10 erros
                    print(f"   {error}")
                if len(errors) > 10:
                    print(f"   ... e mais {len(errors) - 10} erros")
            
            print(f"\n✅ Importação concluída!")
            
    except Exception as e:
        print(f"❌ Erro durante a importação: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    # Caminho para o arquivo CSV
    csv_file = "../csv/Fluxo de Caixa 2025_Cliente teste - Lançamentos Previstos.csv"
    
    # Nome da Business Unit (pode ser alterado)
    bu_name = "Matriz"
    
    print("🔍 IMPORTADOR DE PREVISÕES FINANCEIRAS")
    print("=" * 50)
    
    import_forecasts(csv_file, bu_name)
