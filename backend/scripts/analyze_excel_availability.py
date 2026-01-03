#!/usr/bin/env python3
"""
Script para analisar a planilha Excel e identificar contas de disponibilidade
(Bancos, Caixa, Investimentos) que deveriam aparecer no dashboard.
"""

import sys
import os
from pathlib import Path
import pandas as pd
from decimal import Decimal

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"

def find_sheet_in_excel(excel_file: Path, sheet_names: list) -> str:
    """Encontra a primeira aba que existe no Excel"""
    try:
        xls = pd.ExcelFile(excel_file)
        for name in sheet_names:
            if name in xls.sheet_names:
                return name
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
    return None

def read_excel_sheet(excel_file: Path, sheet_name: str) -> pd.DataFrame:
    """Lê uma aba do Excel"""
    try:
        return pd.read_excel(excel_file, sheet_name=sheet_name)
    except Exception as e:
        print(f"❌ Erro ao ler aba {sheet_name}: {e}")
        return pd.DataFrame()

def analyze_plano_contas(excel_file: Path):
    """Analisa o plano de contas para encontrar contas de disponibilidade"""
    print("="*80)
    print("📊 ANÁLISE DO PLANO DE CONTAS - DISPONIBILIDADES")
    print("="*80)
    
    # Encontrar aba
    sheet_names = ["Plano de contas|LLM", "Plano de contas", "Plano de Contas", "Plano de Contas|LLM"]
    sheet_name = find_sheet_in_excel(excel_file, sheet_names)
    if not sheet_name:
        print("❌ Aba do Plano de Contas não encontrada")
        return
    
    print(f"✅ Aba encontrada: {sheet_name}")
    print()
    
    # Ler dados
    df = read_excel_sheet(excel_file, sheet_name)
    if df.empty:
        print("❌ Nenhum dado encontrado")
        return
    
    # Normalizar colunas
    df.columns = df.columns.str.strip()
    
    # Mapear colunas
    column_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'conta' in col_lower and 'conta' not in column_map:
            column_map['conta'] = col
        if 'subgrupo' in col_lower and 'subgrupo' not in column_map:
            column_map['subgrupo'] = col
        if 'grupo' in col_lower and 'subgrupo' not in col_lower and 'grupo' not in column_map:
            column_map['grupo'] = col
    
    if 'conta' not in column_map:
        print(f"❌ Coluna 'conta' não encontrada. Colunas: {list(df.columns)}")
        return
    
    print(f"📋 Colunas mapeadas: {column_map}")
    print()
    
    # Palavras-chave para identificar disponibilidades
    bank_keywords = ["banco", "banc", "conta bancária", "conta corrente", "conta poupança", "cc", "cp"]
    cash_keywords = ["caixa", "dinheiro", "cash"]
    investment_keywords = ["investimento", "aplicação", "aplicacao", "cdb", "lci", "lca", "tesouro", "fundo"]
    
    # Excluir palavras que indicam que NÃO é disponibilidade
    exclude_keywords = ["despesa", "custo", "tarifa", "taxa", "pagamento", "compra", "saída", "saida", 
                        "empréstimo", "emprestimo", "máquina", "maquina", "equipamento"]
    
    banks = []
    cash = []
    investments = []
    
    for idx, row in df.iterrows():
        conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
        subgrupo_nome = str(row[column_map.get('subgrupo', '')]).strip() if 'subgrupo' in column_map and pd.notna(row[column_map['subgrupo']]) else ""
        grupo_nome = str(row[column_map.get('grupo', '')]).strip() if 'grupo' in column_map and pd.notna(row[column_map['grupo']]) else ""
        
        if not conta_nome:
            continue
        
        conta_lower = conta_nome.lower()
        combined = f"{conta_lower} {subgrupo_nome.lower()} {grupo_nome.lower()}"
        
        # Excluir se tiver palavras de exclusão
        if any(exclude in combined for exclude in exclude_keywords):
            continue
        
        # Excluir se estiver em grupos de despesa/custo/receita
        grupo_lower = grupo_nome.lower()
        subgrupo_lower = subgrupo_nome.lower()
        if any(keyword in grupo_lower for keyword in ["despesa", "custo", "receita", "dedução"]):
            continue
        if any(keyword in subgrupo_lower for keyword in ["despesa", "custo", "receita", "dedução"]):
            continue
        
        # Excluir movimentações não operacionais (saídas)
        if "movimentação" in grupo_lower or "movimentacao" in grupo_lower:
            if "saída" in subgrupo_lower or "saida" in subgrupo_lower:
                continue
        
        # Excluir investimentos em bens materiais
        if "investimento" in grupo_lower:
            if "bens" in subgrupo_lower or "material" in subgrupo_lower:
                continue
        
        # Classificar
        item = {
            "conta": conta_nome,
            "subgrupo": subgrupo_nome,
            "grupo": grupo_nome,
        }
        
        # Bancos
        if any(keyword in conta_lower for keyword in bank_keywords):
            banks.append(item)
        # Caixa
        elif any(keyword in conta_lower for keyword in cash_keywords):
            cash.append(item)
        # Investimentos
        elif any(keyword in conta_lower for keyword in investment_keywords):
            investments.append(item)
    
    # Mostrar resultados
    print("="*80)
    print("🏦 CONTAS BANCÁRIAS ENCONTRADAS NA PLANILHA")
    print("="*80)
    if banks:
        for item in banks:
            print(f"  • {item['conta']}")
            print(f"    Grupo: {item['grupo']} / Subgrupo: {item['subgrupo']}")
            print()
    else:
        print("  (nenhuma conta bancária encontrada)")
    print()
    
    print("="*80)
    print("💵 CONTAS DE CAIXA ENCONTRADAS NA PLANILHA")
    print("="*80)
    if cash:
        for item in cash:
            print(f"  • {item['conta']}")
            print(f"    Grupo: {item['grupo']} / Subgrupo: {item['subgrupo']}")
            print()
    else:
        print("  (nenhuma conta de caixa encontrada)")
    print()
    
    print("="*80)
    print("📈 CONTAS DE INVESTIMENTO ENCONTRADAS NA PLANILHA")
    print("="*80)
    if investments:
        for item in investments:
            print(f"  • {item['conta']}")
            print(f"    Grupo: {item['grupo']} / Subgrupo: {item['subgrupo']}")
            print()
    else:
        print("  (nenhuma conta de investimento encontrada)")
    print()
    
    print("="*80)
    print("📊 RESUMO")
    print("="*80)
    print(f"Total de contas bancárias: {len(banks)}")
    print(f"Total de contas de caixa: {len(cash)}")
    print(f"Total de contas de investimento: {len(investments)}")
    print()
    
    return {
        "banks": banks,
        "cash": cash,
        "investments": investments
    }

def analyze_lancamentos_diarios(excel_file: Path):
    """Analisa lançamentos diários para ver valores de disponibilidade"""
    print("="*80)
    print("💰 ANÁLISE DE LANÇAMENTOS DIÁRIOS - DISPONIBILIDADES")
    print("="*80)
    
    sheet_names = ["Lançamento Diário", "Lançamento Diario", "Lancamento Diario", "Lançamentos Diários"]
    sheet_name = find_sheet_in_excel(excel_file, sheet_names)
    if not sheet_name:
        print("❌ Aba de Lançamentos Diários não encontrada")
        return
    
    print(f"✅ Aba encontrada: {sheet_name}")
    print()
    
    df = read_excel_sheet(excel_file, sheet_name)
    if df.empty:
        print("❌ Nenhum dado encontrado")
        return
    
    # Normalizar colunas
    df.columns = df.columns.str.strip()
    
    # Mapear colunas
    column_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'conta' in col_lower and 'conta' not in column_map:
            column_map['conta'] = col
        if 'valor' in col_lower and 'valor' not in column_map:
            column_map['valor'] = col
        if 'tipo' in col_lower and 'tipo' not in column_map:
            column_map['tipo'] = col
    
    print(f"📋 Colunas mapeadas: {column_map}")
    print()
    
    if 'conta' not in column_map:
        print("❌ Coluna 'conta' não encontrada")
        return
    
    # Buscar contas de disponibilidade
    bank_keywords = ["banco", "banc", "conta bancária", "conta corrente"]
    cash_keywords = ["caixa", "dinheiro"]
    investment_keywords = ["investimento", "aplicação"]
    
    bank_lancamentos = []
    cash_lancamentos = []
    investment_lancamentos = []
    
    for idx, row in df.iterrows():
        conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
        if not conta_nome:
            continue
        
        conta_lower = conta_nome.lower()
        
        # Buscar valor se existir
        valor = 0
        if 'valor' in column_map and pd.notna(row[column_map['valor']]):
            try:
                valor = float(row[column_map['valor']])
            except:
                pass
        
        item = {"conta": conta_nome, "valor": valor}
        
        if any(keyword in conta_lower for keyword in bank_keywords):
            bank_lancamentos.append(item)
        elif any(keyword in conta_lower for keyword in cash_keywords):
            cash_lancamentos.append(item)
        elif any(keyword in conta_lower for keyword in investment_keywords):
            investment_lancamentos.append(item)
    
    print(f"🏦 Lançamentos em contas bancárias: {len(bank_lancamentos)}")
    if bank_lancamentos:
        print("   Contas encontradas:")
        unique_banks = {}
        for item in bank_lancamentos:
            if item['conta'] not in unique_banks:
                unique_banks[item['conta']] = 0
            unique_banks[item['conta']] += item['valor']
        for conta, total in sorted(unique_banks.items()):
            print(f"     • {conta}: R$ {total:,.2f}")
        print()
    
    print(f"💵 Lançamentos em contas de caixa: {len(cash_lancamentos)}")
    if cash_lancamentos:
        print("   Contas encontradas:")
        unique_cash = {}
        for item in cash_lancamentos:
            if item['conta'] not in unique_cash:
                unique_cash[item['conta']] = 0
            unique_cash[item['conta']] += item['valor']
        for conta, total in sorted(unique_cash.items()):
            print(f"     • {conta}: R$ {total:,.2f}")
        print()
    
    print(f"📈 Lançamentos em contas de investimento: {len(investment_lancamentos)}")
    if investment_lancamentos:
        print("   Contas encontradas:")
        unique_inv = {}
        for item in investment_lancamentos:
            if item['conta'] not in unique_inv:
                unique_inv[item['conta']] = 0
            unique_inv[item['conta']] += item['valor']
        for conta, total in sorted(unique_inv.items()):
            print(f"     • {conta}: R$ {total:,.2f}")
        print()

def main():
    if not EXCEL_FILE.exists():
        print(f"❌ Arquivo Excel não encontrado: {EXCEL_FILE}")
        return
    
    print(f"📁 Analisando: {EXCEL_FILE}")
    print()
    
    # Analisar plano de contas
    disponibilidades = analyze_plano_contas(EXCEL_FILE)
    
    # Analisar lançamentos
    analyze_lancamentos_diarios(EXCEL_FILE)
    
    print("="*80)
    print("✅ Análise concluída!")
    print("="*80)
    print()
    print("💡 PRÓXIMOS PASSOS:")
    print("  1. Verificar se essas contas estão no banco de dados")
    print("  2. Verificar se estão sendo classificadas corretamente pela função _classify_account_type")
    print("  3. Ajustar a lógica de classificação se necessário")

if __name__ == "__main__":
    main()

