#!/usr/bin/env python3
"""
Script para verificar o status das contas de liquidação e lançamentos associados
"""
import os
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import func
from app.database import SessionLocal
from app.models.liquidation_accounts import LiquidationAccount, LiquidationAccountType
from app.models.lancamento_diario import LancamentoDiario, TransactionType, TransactionStatus
from app.models.auth import Tenant, BusinessUnit
from decimal import Decimal

def check_liquidation_status():
    """Verifica o status das contas de liquidação"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("🔍 VERIFICAÇÃO DE CONTAS DE LIQUIDAÇÃO")
        print("=" * 70)
        print()
        
        # 1. Verificar contas de liquidação criadas
        print("1️⃣ Contas de Liquidação no Banco:")
        liquidation_accounts = db.query(LiquidationAccount).all()
        print(f"   Total de contas: {len(liquidation_accounts)}")
        
        if liquidation_accounts:
            for acc in liquidation_accounts:
                print(f"   - {acc.code}: {acc.name} (tipo: {acc.account_type.value})")
        else:
            print("   ⚠️  Nenhuma conta de liquidação encontrada!")
        print()
        
        # 2. Verificar lançamentos com liquidation_account_id
        print("2️⃣ Lançamentos com liquidation_account_id:")
        total_lancamentos = db.query(LancamentoDiario).count()
        lancamentos_com_liquidation = db.query(LancamentoDiario).filter(
            LancamentoDiario.liquidation_account_id.isnot(None)
        ).count()
        lancamentos_sem_liquidation = total_lancamentos - lancamentos_com_liquidation
        
        print(f"   Total de lançamentos: {total_lancamentos}")
        print(f"   Com liquidation_account_id: {lancamentos_com_liquidation}")
        print(f"   Sem liquidation_account_id: {lancamentos_sem_liquidation}")
        print()
        
        # 3. Verificar distribuição por código de liquidação
        if lancamentos_com_liquidation > 0:
            print("3️⃣ Distribuição por código de liquidação:")
            query = (
                db.query(
                    LiquidationAccount.code,
                    LiquidationAccount.account_type,
                    func.count(LancamentoDiario.id).label("count")
                )
                .join(LancamentoDiario, LiquidationAccount.id == LancamentoDiario.liquidation_account_id)
                .group_by(LiquidationAccount.code, LiquidationAccount.account_type)
            )
            
            for row in query.all():
                print(f"   - {row.code} ({row.account_type.value}): {row.count} lançamentos")
            print()
        
        # 4. Verificar saldos calculados
        print("4️⃣ Saldos Calculados por Tipo:")
        if lancamentos_com_liquidation > 0:
            from app.models.lancamento_diario import LancamentoDiario
            from datetime import date
            
            today = date.today()
            
            # Calcular saldos por tipo
            query = (
                db.query(
                    LiquidationAccount.account_type,
                    func.sum(
                        func.case(
                            (LancamentoDiario.transaction_type == TransactionType.RECEITA, LancamentoDiario.valor),
                            else_=-LancamentoDiario.valor
                        )
                    ).label("saldo")
                )
                .join(LiquidationAccount, LancamentoDiario.liquidation_account_id == LiquidationAccount.id)
                .filter(
                    LancamentoDiario.is_active.is_(True),
                    LancamentoDiario.status != TransactionStatus.CANCELADO,
                    func.date(LancamentoDiario.data_movimentacao) <= today
                )
                .group_by(LiquidationAccount.account_type)
            )
            
            banks_total = Decimal(0)
            cash_total = Decimal(0)
            investments_total = Decimal(0)
            
            for row in query.all():
                saldo = row.saldo or Decimal(0)
                if row.account_type == LiquidationAccountType.BANK_ACCOUNT:
                    banks_total = saldo
                    print(f"   Bancos: R$ {banks_total:,.2f}")
                elif row.account_type == LiquidationAccountType.CASH:
                    cash_total = saldo
                    print(f"   Caixa: R$ {cash_total:,.2f}")
                elif row.account_type == LiquidationAccountType.INVESTMENT:
                    investments_total = saldo
                    print(f"   Investimentos: R$ {investments_total:,.2f}")
            
            total = banks_total + cash_total + investments_total
            print(f"   Total: R$ {total:,.2f}")
        else:
            print("   ⚠️  Nenhum lançamento com conta de liquidação para calcular saldos")
        print()
        
        # 5. Diagnóstico
        print("5️⃣ Diagnóstico:")
        if len(liquidation_accounts) == 0:
            print("   ❌ PROBLEMA: Nenhuma conta de liquidação foi criada")
            print("   ✅ SOLUÇÃO: Executar re-seed para criar as contas")
        elif lancamentos_com_liquidation == 0:
            print("   ❌ PROBLEMA: Contas de liquidação existem, mas não estão associadas aos lançamentos")
            print("   ✅ SOLUÇÃO: Executar re-seed para associar os lançamentos")
        elif lancamentos_com_liquidation < total_lancamentos * 0.9:
            print(f"   ⚠️  ATENÇÃO: Apenas {lancamentos_com_liquidation}/{total_lancamentos} lançamentos têm conta de liquidação")
            print("   ✅ SOLUÇÃO: Executar re-seed para associar os lançamentos restantes")
        else:
            print("   ✅ Tudo parece estar correto!")
            print(f"   ✅ {lancamentos_com_liquidation}/{total_lancamentos} lançamentos têm conta de liquidação")
        
        print()
        print("=" * 70)
        
    finally:
        db.close()

if __name__ == "__main__":
    check_liquidation_status()

