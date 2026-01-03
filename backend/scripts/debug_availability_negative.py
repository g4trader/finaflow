#!/usr/bin/env python3
"""
Script para debugar por que o saldo de disponibilidades está negativo
"""

import sys
import os
from pathlib import Path
from decimal import Decimal
from datetime import date

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.database import SessionLocal
from app.models.lancamento_diario import LancamentoDiario, TransactionType, TransactionStatus
from app.models.chart_of_accounts import ChartAccount

def _classify_account_type(account_name: str, account_code: str = "") -> str:
    """Classifica o tipo de conta"""
    name_lower = account_name.lower().strip()
    code_lower = (account_code or "").lower().strip()
    combined = f"{name_lower} {code_lower}"
    
    bank_keywords = ["banco", "banc", "conta bancária", "conta corrente", "conta poupança", "cc", "cp"]
    if any(keyword in combined for keyword in bank_keywords):
        return "BANK"
    
    cash_keywords = ["caixa", "dinheiro", "cash", "cx", "caixa físico", "caixa fisico"]
    if any(keyword in combined for keyword in cash_keywords):
        return "CASH"
    
    investment_keywords = ["investimento", "aplicação", "aplicacao", "invest", "cdb", "lci", "lca", "tesouro", "fundo"]
    if any(keyword in combined for keyword in investment_keywords):
        return "INVESTMENT"
    
    return None

def main():
    db: Session = SessionLocal()
    today = date.today()
    
    # Buscar tenant (assumindo que existe)
    tenant_id = os.getenv("TENANT_ID", "finaflow-staging-tenant-id")
    business_unit_id = os.getenv("BUSINESS_UNIT_ID", None)
    
    print("="*80)
    print("🔍 DEBUG: Saldo Negativo de Disponibilidades")
    print("="*80)
    print(f"📅 Data de corte: {today}")
    print(f"🏢 Tenant ID: {tenant_id}")
    print(f"🏭 Business Unit ID: {business_unit_id or 'N/A'}")
    print()
    
    # Buscar todos os lançamentos realizados até hoje
    lancamentos_query = (
        db.query(
            LancamentoDiario.conta_id,
            ChartAccount.name.label("conta_nome"),
            ChartAccount.code.label("conta_codigo"),
            func.sum(
                case(
                    (LancamentoDiario.transaction_type == TransactionType.RECEITA, LancamentoDiario.valor),
                    else_=-LancamentoDiario.valor
                )
            ).label("saldo"),
            func.count(LancamentoDiario.id).label("qtd_lancamentos"),
            func.sum(
                case(
                    (LancamentoDiario.transaction_type == TransactionType.RECEITA, LancamentoDiario.valor),
                    else_=0
                )
            ).label("total_receitas"),
            func.sum(
                case(
                    (LancamentoDiario.transaction_type.in_([TransactionType.DESPESA, TransactionType.CUSTO]), LancamentoDiario.valor),
                    else_=0
                )
            ).label("total_despesas_custos")
        )
        .join(ChartAccount, LancamentoDiario.conta_id == ChartAccount.id)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.is_active.is_(True),
            LancamentoDiario.status != TransactionStatus.CANCELADO,
            func.date(LancamentoDiario.data_movimentacao) <= today,
        )
        .group_by(LancamentoDiario.conta_id, ChartAccount.name, ChartAccount.code)
    )
    
    if business_unit_id:
        lancamentos_query = lancamentos_query.filter(
            LancamentoDiario.business_unit_id == business_unit_id
        )
    
    lancamentos = lancamentos_query.all()
    
    print(f"📊 Total de contas com lançamentos: {len(lancamentos)}")
    print()
    
    # Separar por tipo
    banks = []
    cash = []
    investments = []
    unclassified = []
    
    for lanc in lancamentos:
        account_type = _classify_account_type(lanc.conta_nome, lanc.conta_codigo)
        saldo = lanc.saldo or Decimal(0)
        
        item = {
            "conta": lanc.conta_nome,
            "codigo": lanc.conta_codigo,
            "saldo": saldo,
            "qtd": lanc.qtd_lancamentos or 0,
            "receitas": lanc.total_receitas or Decimal(0),
            "despesas_custos": lanc.total_despesas_custos or Decimal(0),
        }
        
        if account_type == "BANK":
            banks.append(item)
        elif account_type == "CASH":
            cash.append(item)
        elif account_type == "INVESTMENT":
            investments.append(item)
        else:
            unclassified.append(item)
    
    # Mostrar resultados
    print("="*80)
    print("🏦 BANCOS")
    print("="*80)
    banks_total = Decimal(0)
    for item in banks:
        banks_total += item["saldo"]
        print(f"  {item['conta']} ({item['codigo']}):")
        print(f"    Saldo: R$ {item['saldo']:,.2f}")
        print(f"    Receitas: R$ {item['receitas']:,.2f}")
        print(f"    Despesas/Custos: R$ {item['despesas_custos']:,.2f}")
        print(f"    Qtd lançamentos: {item['qtd']}")
        print()
    print(f"  TOTAL BANCOS: R$ {banks_total:,.2f}")
    print()
    
    print("="*80)
    print("💵 CAIXA/DINHEIRO")
    print("="*80)
    cash_total = Decimal(0)
    for item in cash:
        cash_total += item["saldo"]
        print(f"  {item['conta']} ({item['codigo']}):")
        print(f"    Saldo: R$ {item['saldo']:,.2f}")
        print(f"    Receitas: R$ {item['receitas']:,.2f}")
        print(f"    Despesas/Custos: R$ {item['despesas_custos']:,.2f}")
        print(f"    Qtd lançamentos: {item['qtd']}")
        print()
    print(f"  TOTAL CAIXA: R$ {cash_total:,.2f}")
    print()
    
    print("="*80)
    print("📈 INVESTIMENTOS")
    print("="*80)
    investments_total = Decimal(0)
    for item in investments:
        investments_total += item["saldo"]
        print(f"  {item['conta']} ({item['codigo']}):")
        print(f"    Saldo: R$ {item['saldo']:,.2f}")
        print(f"    Receitas: R$ {item['receitas']:,.2f}")
        print(f"    Despesas/Custos: R$ {item['despesas_custos']:,.2f}")
        print(f"    Qtd lançamentos: {item['qtd']}")
        print()
    print(f"  TOTAL INVESTIMENTOS: R$ {investments_total:,.2f}")
    print()
    
    total = banks_total + cash_total + investments_total
    print("="*80)
    print("📊 RESUMO")
    print("="*80)
    print(f"Bancos:        R$ {banks_total:,.2f}")
    print(f"Caixa:         R$ {cash_total:,.2f}")
    print(f"Investimentos: R$ {investments_total:,.2f}")
    print(f"TOTAL:         R$ {total:,.2f}")
    print()
    
    if total < 0:
        print("⚠️  SALDO NEGATIVO DETECTADO!")
        print()
        print("🔍 Possíveis causas:")
        print("  1. Mais despesas/custos do que receitas nas contas de disponibilidade")
        print("  2. Contas classificadas incorretamente (não são realmente disponibilidade)")
        print("  3. Lógica de cálculo invertida")
        print("  4. Lançamentos com valores incorretos")
        print()
    
    # Mostrar algumas contas não classificadas (para debug)
    if unclassified and len(unclassified) <= 10:
        print("="*80)
        print("❓ CONTAS NÃO CLASSIFICADAS (primeiras 10)")
        print("="*80)
        for item in unclassified[:10]:
            print(f"  {item['conta']} ({item['codigo']}): R$ {item['saldo']:,.2f}")
        print()
    
    db.close()

if __name__ == "__main__":
    main()




