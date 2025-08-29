#!/usr/bin/env python3
"""
Script para importar dados CSV para PostgreSQL
"""

import sys
import os
import csv
import re
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.financial import (
    AccountGroup, AccountSubgroup, Account, Transaction
)
from app.services.security import SecurityService
from uuid import uuid4

def parse_currency(value_str):
    """Converte string de moeda para decimal."""
    if not value_str or value_str.strip() == '':
        return Decimal('0.00')
    
    # Remove caracteres não numéricos exceto vírgula e ponto
    cleaned = re.sub(r'[^\d,.-]', '', value_str.strip())
    
    # Substitui vírgula por ponto para decimal
    cleaned = cleaned.replace(',', '.')
    
    try:
        return Decimal(cleaned)
    except:
        return Decimal('0.00')

def parse_date(date_str):
    """Converte string de data para datetime."""
    if not date_str or date_str.strip() == '':
        return None
    
    try:
        # Formato: DD/MM/YYYY
        return datetime.strptime(date_str.strip(), '%d/%m/%Y')
    except:
        return None

def import_account_structure():
    """Importa estrutura de contas do CSV."""
    print("📊 Importando estrutura de contas...")
    
    db = SessionLocal()
    
    try:
        # Buscar tenant padrão
        tenant = db.query(Tenant).first()
        if not tenant:
            print("❌ Tenant não encontrado. Execute init_database.py primeiro.")
            return
        
        # Buscar super admin
        admin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        if not admin:
            print("❌ Super admin não encontrado. Execute init_database.py primeiro.")
            return
        
        csv_file = Path(__file__).parent.parent / "csv" / "Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"
        
        if not csv_file.exists():
            print(f"❌ Arquivo CSV não encontrado: {csv_file}")
            return
        
        # Mapeamento de tipos de conta
        account_type_mapping = {
            'Receita': 'revenue',
            'Receita Financeira': 'revenue',
            'Deduções': 'expense',
            'Custos': 'cost',
            'Despesas Operacionais': 'expense',
            'Investimentos': 'asset',
            'Movimentações Não Operacionais': 'expense'
        }
        
        # Dicionários para cache
        groups_cache = {}
        subgroups_cache = {}
        accounts_cache = {}
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                conta = row.get('Conta', '').strip()
                subgrupo = row.get('Subgrupo', '').strip()
                grupo = row.get('Grupo', '').strip()
                escolha = row.get('Escolha', '').strip()
                
                if not conta or escolha != 'Usar':
                    continue
                
                # Criar ou buscar grupo
                if grupo not in groups_cache:
                    existing_group = db.query(AccountGroup).filter(
                        AccountGroup.tenant_id == tenant.id,
                        AccountGroup.name == grupo
                    ).first()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group
                    else:
                        group = AccountGroup(
                            tenant_id=tenant.id,
                            name=grupo,
                            code=grupo.replace(' ', '_').upper()[:20],
                            description=f"Grupo: {grupo}"
                        )
                        db.add(group)
                        db.commit()
                        db.refresh(group)
                        groups_cache[grupo] = group
                        print(f"✅ Grupo criado: {grupo}")
                
                # Criar ou buscar subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    existing_subgroup = db.query(AccountSubgroup).filter(
                        AccountSubgroup.tenant_id == tenant.id,
                        AccountSubgroup.name == subgrupo
                    ).first()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup
                    else:
                        subgroup = AccountSubgroup(
                            tenant_id=tenant.id,
                            group_id=groups_cache[grupo].id,
                            name=subgrupo,
                            code=subgrupo.replace(' ', '_').upper()[:20],
                            description=f"Subgrupo: {subgrupo}"
                        )
                        db.add(subgroup)
                        db.commit()
                        db.refresh(subgroup)
                        subgroups_cache[subgroup_key] = subgroup
                        print(f"✅ Subgrupo criado: {subgrupo}")
                
                # Criar ou buscar conta
                if conta not in accounts_cache:
                    existing_account = db.query(Account).filter(
                        Account.tenant_id == tenant.id,
                        Account.name == conta
                    ).first()
                    
                    if existing_account:
                        accounts_cache[conta] = existing_account
                    else:
                        account_type = account_type_mapping.get(grupo, 'expense')
                        account = Account(
                            tenant_id=tenant.id,
                            subgroup_id=subgroups_cache[subgroup_key].id,
                            name=conta,
                            code=conta.replace(' ', '_').upper()[:20],
                            description=f"Conta: {conta}",
                            account_type=account_type
                        )
                        db.add(account)
                        db.commit()
                        db.refresh(account)
                        accounts_cache[conta] = account
                        print(f"✅ Conta criada: {conta}")
        
        print(f"✅ Estrutura de contas importada: {len(groups_cache)} grupos, {len(subgroups_cache)} subgrupos, {len(accounts_cache)} contas")
        
    except Exception as e:
        print(f"❌ Erro ao importar estrutura de contas: {e}")
        db.rollback()
    finally:
        db.close()

def import_transactions():
    """Importa transações do CSV."""
    print("💰 Importando transações...")
    
    db = SessionLocal()
    
    try:
        # Buscar tenant e admin
        tenant = db.query(Tenant).first()
        admin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        
        if not tenant or not admin:
            print("❌ Tenant ou admin não encontrado.")
            return
        
        # Buscar todas as contas e subgrupos
        accounts = {acc.name: acc for acc in db.query(Account).filter(Account.tenant_id == tenant.id).all()}
        subgroups = {sg.name: sg for sg in db.query(AccountSubgroup).filter(AccountSubgroup.tenant_id == tenant.id).all()}
        
        csv_file = Path(__file__).parent.parent / "csv" / "Fluxo de Caixa 2025_Cliente teste - Lançamento Diário.csv"
        
        if not csv_file.exists():
            print(f"❌ Arquivo CSV não encontrado: {csv_file}")
            return
        
        transactions_imported = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                data = row.get('Data Movimentação', '').strip()
                conta = row.get('Subgrupo', '').strip()  # O nome da conta está na coluna Subgrupo
                valor = row.get('Valor', '').strip()
                grupo = row.get('Grupo', '').strip()
                
                if not data or not conta or not valor:
                    continue
                
                # Buscar conta ou subgrupo
                account = accounts.get(conta)
                if not account:
                    # Se não encontrar a conta específica, buscar pelo subgrupo
                    subgroup = subgroups.get(conta)
                    if subgroup:
                        # Buscar uma conta do subgrupo
                        account = db.query(Account).filter(
                            Account.tenant_id == tenant.id,
                            Account.subgroup_id == subgroup.id
                        ).first()
                
                if not account:
                    print(f"⚠️ Conta não encontrada: {conta}")
                    continue
                
                # Parsear valores
                amount = parse_currency(valor)
                transaction_date = parse_date(data)
                
                # Determinar tipo de transação baseado no grupo
                if grupo in ['Receita', 'Receita Financeira', 'Entradas não Operacionais']:
                    transaction_type = "credit"
                else:
                    transaction_type = "debit"
                
                # Criar transação
                transaction = Transaction(
                    id=str(uuid4()),
                    tenant_id=tenant.id,
                    account_id=account.id,
                    description=f"Transação {conta}",
                    amount=amount,
                    transaction_date=transaction_date,
                    transaction_type=transaction_type,
                    created_by=admin.id
                )
                
                db.add(transaction)
                transactions_imported += 1
                
                if transactions_imported % 100 == 0:
                    print(f"📊 {transactions_imported} transações processadas...")
        
        db.commit()
        print(f"✅ Total de {transactions_imported} transações importadas")
        
    except Exception as e:
        print(f"❌ Erro ao importar transações: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Função principal."""
    print("🚀 Iniciando importação de dados CSV...")
    
    # Importar estrutura de contas
    import_account_structure()
    
    # Importar transações
    import_transactions()
    
    print("🎉 Importação concluída!")

if __name__ == "__main__":
    main()
