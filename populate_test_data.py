#!/usr/bin/env python3
"""
Popular banco de dados com dados de teste baseados na metodologia Ana Paula
"""

from app.database import get_db
from app.models.auth import User, UserRole, UserStatus, Tenant
from app.models.financial import (
    AccountGroup, AccountSubgroup, Account, Transaction, 
    BankAccount, CashFlow
)
from app.models.auth import BusinessUnit, Department
from app.services.security import SecurityService
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta
import random

def create_test_data():
    """Criar dados de teste baseados na metodologia Ana Paula"""
    
    db = next(get_db())
    
    print("🏢 Criando estrutura organizacional...")
    
    # Criar tenant principal
    tenant = db.query(Tenant).first()
    if not tenant:
        tenant = Tenant(
            name="Empresa Demo Ana Paula",
            domain="demo.finaflow.com"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    
    # Criar unidade de negócio
    business_unit = BusinessUnit(
        tenant_id=tenant.id,
        name="Matriz",
        code="MATRIZ"
    )
    db.add(business_unit)
    db.commit()
    db.refresh(business_unit)
    
    # Criar departamento
    department = Department(
        business_unit_id=business_unit.id,
        name="Financeiro",
        code="FIN"
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    
    print("📊 Criando estrutura de contas baseada na metodologia Ana Paula...")
    
    # Grupos de contas baseados na planilha
    groups_data = [
        {"name": "Receita", "code": "REC", "description": "Receitas Operacionais"},
        {"name": "Receita Financeira", "code": "REC_FIN", "description": "Receitas Financeiras"},
        {"name": "Deduções", "code": "DED", "description": "Deduções da Receita"},
        {"name": "Custos", "code": "CUST", "description": "Custos Operacionais"},
        {"name": "Despesas Operacionais", "code": "DESP_OP", "description": "Despesas Operacionais"},
        {"name": "Despesas Financeiras", "code": "DESP_FIN", "description": "Despesas Financeiras"},
        {"name": "Investimentos", "code": "INV", "description": "Investimentos"},
        {"name": "Patrimônio", "code": "PAT", "description": "Patrimônio Líquido"}
    ]
    
    groups = {}
    for group_data in groups_data:
        group = AccountGroup(
            tenant_id=tenant.id,
            name=group_data["name"],
            code=group_data["code"],
            description=group_data["description"]
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        groups[group_data["code"]] = group
    
    # Subgrupos baseados na planilha Ana Paula
    subgroups_data = [
        {"group_code": "REC", "name": "Receita", "code": "REC_001"},
        {"group_code": "REC_FIN", "name": "Receita Financeira", "code": "REC_FIN_001"},
        {"group_code": "DED", "name": "Deduções da receita", "code": "DED_001"},
        {"group_code": "CUST", "name": "Custos com Mercadorias Vendidas", "code": "CUST_001"},
        {"group_code": "CUST", "name": "Custos com Serviços Prestados", "code": "CUST_002"},
        {"group_code": "DESP_OP", "name": "Despesas com Pessoal", "code": "DESP_OP_001"},
        {"group_code": "DESP_OP", "name": "Despesas Comerciais", "code": "DESP_OP_002"},
        {"group_code": "DESP_OP", "name": "Despesas Marketing", "code": "DESP_OP_003"},
        {"group_code": "DESP_OP", "name": "Despesas Administrativas", "code": "DESP_OP_004"},
        {"group_code": "DESP_FIN", "name": "Despesas Financeiras", "code": "DESP_FIN_001"},
        {"group_code": "INV", "name": "Investimentos", "code": "INV_001"},
        {"group_code": "PAT", "name": "Patrimônio Líquido", "code": "PAT_001"}
    ]
    
    subgroups = {}
    for subgroup_data in subgroups_data:
        subgroup = AccountSubgroup(
            tenant_id=tenant.id,
            group_id=groups[subgroup_data["group_code"]].id,
            name=subgroup_data["name"],
            code=subgroup_data["code"]
        )
        db.add(subgroup)
        db.commit()
        db.refresh(subgroup)
        subgroups[subgroup_data["code"]] = subgroup
    
    print("💰 Criando contas específicas baseadas na planilha...")
    
    # Contas específicas da metodologia Ana Paula
    accounts_data = [
        # Receitas
        {"subgroup_code": "REC_001", "name": "Vendas Cursos pelo Comercial", "code": "REC_001_001"},
        {"subgroup_code": "REC_001", "name": "Treinamentos B2B", "code": "REC_001_002"},
        {"subgroup_code": "REC_001", "name": "Treinamentos e Consultorias B2B", "code": "REC_001_003"},
        {"subgroup_code": "REC_001", "name": "Vendas B2C - Marketing", "code": "REC_001_004"},
        {"subgroup_code": "REC_001", "name": "Venda B2C - Comercial", "code": "REC_001_005"},
        {"subgroup_code": "REC_001", "name": "Marketing B2B para Clientes", "code": "REC_001_006"},
        {"subgroup_code": "REC_001", "name": "Vendas de Ferramentas", "code": "REC_001_007"},
        {"subgroup_code": "REC_001", "name": "Outras Receitas", "code": "REC_001_008"},
        
        # Receitas Financeiras
        {"subgroup_code": "REC_FIN_001", "name": "Rendimentos de Aplicações Financeiras", "code": "REC_FIN_001_001"},
        {"subgroup_code": "REC_FIN_001", "name": "Juros e Descontos Obtidos", "code": "REC_FIN_001_002"},
        
        # Deduções
        {"subgroup_code": "DED_001", "name": "Simples Nacional", "code": "DED_001_001"},
        {"subgroup_code": "DED_001", "name": "Parcelamento Simples", "code": "DED_001_002"},
        
        # Custos
        {"subgroup_code": "CUST_001", "name": "Fornecedores", "code": "CUST_001_001"},
        {"subgroup_code": "CUST_001", "name": "Compra de Ferramentas para Vendas", "code": "CUST_001_002"},
        {"subgroup_code": "CUST_002", "name": "Alimentação Prestação de Serviços", "code": "CUST_002_001"},
        {"subgroup_code": "CUST_002", "name": "Locação de Veículos", "code": "CUST_002_002"},
        {"subgroup_code": "CUST_002", "name": "Materiais para Treinamentos", "code": "CUST_002_003"},
        {"subgroup_code": "CUST_002", "name": "Serviços de Terceiros", "code": "CUST_002_004"},
        {"subgroup_code": "CUST_002", "name": "Hotel Prestação de Serviços", "code": "CUST_002_005"},
        {"subgroup_code": "CUST_002", "name": "Passagem Aérea", "code": "CUST_002_006"},
        {"subgroup_code": "CUST_002", "name": "Comissão Parceiros", "code": "CUST_002_007"},
        {"subgroup_code": "CUST_002", "name": "Comissão Junior", "code": "CUST_002_008"},
        {"subgroup_code": "CUST_002", "name": "Comissão Otávio", "code": "CUST_002_009"},
        
        # Despesas com Pessoal
        {"subgroup_code": "DESP_OP_001", "name": "Salários e Ordenados", "code": "DESP_OP_001_001"},
        {"subgroup_code": "DESP_OP_001", "name": "13º Salário", "code": "DESP_OP_001_002"},
        {"subgroup_code": "DESP_OP_001", "name": "Férias", "code": "DESP_OP_001_003"},
        {"subgroup_code": "DESP_OP_001", "name": "INSS", "code": "DESP_OP_001_004"},
        {"subgroup_code": "DESP_OP_001", "name": "FGTS", "code": "DESP_OP_001_005"},
        {"subgroup_code": "DESP_OP_001", "name": "Treinamento e Desenvolvimento", "code": "DESP_OP_001_006"},
        {"subgroup_code": "DESP_OP_001", "name": "Confraternização", "code": "DESP_OP_001_007"},
        {"subgroup_code": "DESP_OP_001", "name": "Consultoria de Recursos Humanos", "code": "DESP_OP_001_008"},
        {"subgroup_code": "DESP_OP_001", "name": "Uniformes e EPIs", "code": "DESP_OP_001_009"},
        
        # Despesas Comerciais
        {"subgroup_code": "DESP_OP_002", "name": "Telefone e Internet - COM", "code": "DESP_OP_002_001"},
        {"subgroup_code": "DESP_OP_002", "name": "Celular - COM", "code": "DESP_OP_002_002"},
        {"subgroup_code": "DESP_OP_002", "name": "Despesas de Viagens - COM", "code": "DESP_OP_002_003"},
        {"subgroup_code": "DESP_OP_002", "name": "Serviços de Terceiros - COM", "code": "DESP_OP_002_004"},
        {"subgroup_code": "DESP_OP_002", "name": "Gasolina / Combustível - COM", "code": "DESP_OP_002_005"},
        {"subgroup_code": "DESP_OP_002", "name": "Estacionamento / Pedágios - COM", "code": "DESP_OP_002_006"},
        {"subgroup_code": "DESP_OP_002", "name": "Eventos com Clientes", "code": "DESP_OP_002_007"},
        {"subgroup_code": "DESP_OP_002", "name": "Brindes", "code": "DESP_OP_002_008"},
        {"subgroup_code": "DESP_OP_002", "name": "Outras Despesas Comerciais", "code": "DESP_OP_002_009"},
        
        # Despesas Marketing
        {"subgroup_code": "DESP_OP_003", "name": "Telefone e Internet - MKT", "code": "DESP_OP_003_001"},
        {"subgroup_code": "DESP_OP_003", "name": "Celular - MKT", "code": "DESP_OP_003_002"},
        {"subgroup_code": "DESP_OP_003", "name": "Despesas de Viagens - MKT", "code": "DESP_OP_003_003"},
        {"subgroup_code": "DESP_OP_003", "name": "Gasolina/Combustível - MKT", "code": "DESP_OP_003_004"},
        {"subgroup_code": "DESP_OP_003", "name": "Estacionamento/Pedágios - MKT", "code": "DESP_OP_003_005"},
        {"subgroup_code": "DESP_OP_003", "name": "Anúncio/Mídias/Propaganda", "code": "DESP_OP_003_006"},
        {"subgroup_code": "DESP_OP_003", "name": "Agências de Marketing e Gestão de Tráfego", "code": "DESP_OP_003_007"},
        {"subgroup_code": "DESP_OP_003", "name": "Realização Eventos", "code": "DESP_OP_003_008"}
    ]
    
    accounts = {}
    for account_data in accounts_data:
        account = Account(
            tenant_id=tenant.id,
            subgroup_id=subgroups[account_data["subgroup_code"]].id,
            name=account_data["name"],
            code=account_data["code"],
            account_type="revenue" if account_data["subgroup_code"].startswith("REC") else "expense"
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        accounts[account_data["code"]] = account
    
    print("🏦 Criando contas bancárias...")
    
    # Contas bancárias
    bank_accounts_data = [
        {"bank_name": "Banco do Brasil", "account_number": "12345-6", "account_type": "checking", "balance": 50000.00},
        {"bank_name": "Caixa Econômica", "account_number": "67890-1", "account_type": "savings", "balance": 25000.00},
        {"bank_name": "Itaú", "account_number": "11111-2", "account_type": "investment", "balance": 100000.00}
    ]
    
    bank_accounts = {}
    for bank_data in bank_accounts_data:
        bank_account = BankAccount(
            tenant_id=tenant.id,
            business_unit_id=business_unit.id,
            bank_name=bank_data["bank_name"],
            account_number=bank_data["account_number"],
            account_type=bank_data["account_type"],
            balance=bank_data["balance"]
        )
        db.add(bank_account)
        db.commit()
        db.refresh(bank_account)
        bank_accounts[bank_data["bank_name"]] = bank_account
    
    print("💳 Criando transações de exemplo...")
    
    # Buscar usuário admin para criar transações
    admin_user = db.query(User).filter(User.username == 'admin').first()
    
    # Criar transações de exemplo para os últimos 3 meses
    transactions_data = []
    base_date = datetime.now() - timedelta(days=90)
    
    # Receitas
    revenue_accounts = ["REC_001_001", "REC_001_002", "REC_001_003", "REC_001_004", "REC_001_005"]
    for i in range(50):
        account_code = random.choice(revenue_accounts)
        amount = random.uniform(1000, 10000)
        date = base_date + timedelta(days=random.randint(0, 90))
        
        transaction = Transaction(
            tenant_id=tenant.id,
            account_id=accounts[account_code].id,
            business_unit_id=business_unit.id,
            amount=amount,
            description=f"Receita {accounts[account_code].name}",
            transaction_date=date,
            transaction_type="credit",
            created_by=admin_user.id
        )
        db.add(transaction)
        transactions_data.append(transaction)
    
    # Despesas
    expense_accounts = ["DESP_OP_001_001", "DESP_OP_002_001", "DESP_OP_003_001", "CUST_001_001", "CUST_002_001"]
    for i in range(80):
        account_code = random.choice(expense_accounts)
        amount = random.uniform(100, 5000)
        date = base_date + timedelta(days=random.randint(0, 90))
        
        transaction = Transaction(
            tenant_id=tenant.id,
            account_id=accounts[account_code].id,
            business_unit_id=business_unit.id,
            amount=-amount,  # Despesas são negativas
            description=f"Despesa {accounts[account_code].name}",
            transaction_date=date,
            transaction_type="debit",
            created_by=admin_user.id
        )
        db.add(transaction)
        transactions_data.append(transaction)
    
    db.commit()
    
    print("📊 Criando fluxo de caixa...")
    
    # Criar fluxo de caixa mensal
    for month in range(3):
        month_date = base_date + timedelta(days=month * 30)
        
        # Calcular receitas e despesas do mês
        month_transactions = [t for t in transactions_data if 
                            t.transaction_date.month == month_date.month and 
                            t.transaction_date.year == month_date.year]
        
        total_revenue = sum(t.amount for t in month_transactions if t.amount > 0)
        total_expenses = abs(sum(t.amount for t in month_transactions if t.amount < 0))
        net_cash_flow = total_revenue - total_expenses
        
        cash_flow = CashFlow(
            tenant_id=tenant.id,
            business_unit_id=business_unit.id,
            date=month_date,
            opening_balance=50000.00,
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            total_costs=0.0,
            net_flow=net_cash_flow,
            closing_balance=float(50000.00) + float(net_cash_flow),
            period_type="monthly"
        )
        db.add(cash_flow)
    
    db.commit()
    
    print("👥 Criando usuários adicionais...")
    
    # Criar usuário financeiro
    finance_user = User(
        tenant_id=tenant.id,
        business_unit_id=business_unit.id,
        department_id=department.id,
        username='financeiro',
        email='financeiro@finaflow.com',
        hashed_password=SecurityService.hash_password('financeiro123'),
        first_name='Maria',
        last_name='Financeira',
        role=UserRole.BUSINESS_UNIT_MANAGER,
        status=UserStatus.ACTIVE
    )
    db.add(finance_user)
    
    # Criar usuário comercial
    sales_user = User(
        tenant_id=tenant.id,
        business_unit_id=business_unit.id,
        username='comercial',
        email='comercial@finaflow.com',
        hashed_password=SecurityService.hash_password('comercial123'),
        first_name='João',
        last_name='Comercial',
        role=UserRole.USER,
        status=UserStatus.ACTIVE
    )
    db.add(sales_user)
    
    db.commit()
    
    print("✅ Dados de teste criados com sucesso!")
    print(f"📊 Resumo:")
    print(f"  - Tenant: {tenant.name}")
    print(f"  - Grupos de contas: {len(groups)}")
    print(f"  - Subgrupos: {len(subgroups)}")
    print(f"  - Contas: {len(accounts)}")
    print(f"  - Contas bancárias: {len(bank_accounts)}")
    print(f"  - Transações: {len(transactions_data)}")
    print(f"  - Usuários: 3 (admin, financeiro, comercial)")
    
    print(f"\n🔑 Credenciais de teste:")
    print(f"  - admin / admin123 (Super Admin)")
    print(f"  - financeiro / financeiro123 (Admin)")
    print(f"  - comercial / comercial123 (Usuário)")

if __name__ == "__main__":
    create_test_data()
