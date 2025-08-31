#!/usr/bin/env python3
"""
Script para importar o plano de contas do CSV
Cria grupos, subgrupos e contas na ordem hierárquica correta
"""
import csv
import os
import sys
from datetime import datetime
from uuid import uuid4

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db, engine
from app.models.auth import Tenant, BusinessUnit
from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, ChartAccount, Base

def create_tables():
    """Criar tabelas do plano de contas se não existirem"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas do plano de contas criadas/verificadas")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False
    return True

def get_tenant_and_bu():
    """Obter tenant e business unit padrão"""
    try:
        db = next(get_db())
        
        # Buscar tenant padrão
        tenant = db.query(Tenant).filter(Tenant.name == "FinaFlow").first()
        if not tenant:
            print("❌ Tenant 'FinaFlow' não encontrado")
            return None, None
        
        # Buscar business unit padrão
        business_unit = db.query(BusinessUnit).filter(
            BusinessUnit.tenant_id == tenant.id,
            BusinessUnit.name == "FinaFlow"
        ).first()
        
        if not business_unit:
            print("❌ Business Unit 'FinaFlow' não encontrado")
            return None, None
        
        print(f"✅ Tenant: {tenant.name} (ID: {tenant.id})")
        print(f"✅ Business Unit: {business_unit.name} (ID: {business_unit.id})")
        
        return tenant, business_unit
        
    except Exception as e:
        print(f"❌ Erro ao buscar tenant/BU: {e}")
        return None, None
    finally:
        db.close()

def import_chart_of_accounts():
    """Importar plano de contas do CSV"""
    print("🚀 Iniciando importação do plano de contas...")
    
    # Criar tabelas
    if not create_tables():
        return False
    
    # Obter tenant e business unit
    tenant, business_unit = get_tenant_and_bu()
    if not tenant or not business_unit:
        return False
    
    # Caminho do arquivo CSV
    csv_file = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo CSV não encontrado: {csv_file}")
        return False
    
    try:
        db = next(get_db())
        
        # Cache para grupos e subgrupos
        groups_cache = {}
        subgroups_cache = {}
        
        # Contadores
        groups_created = 0
        subgroups_created = 0
        accounts_created = 0
        
        with open(csv_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                conta = row.get("Conta", "").strip()
                subgrupo = row.get("Subgrupo", "").strip()
                grupo = row.get("Grupo", "").strip()
                escolha = row.get("Escolha", "").strip().lower()
                
                if not conta or not subgrupo or not grupo:
                    continue
                
                is_active = escolha in ["usar", "sim", "yes", "1", "true"]
                
                # 1. Criar ou obter grupo
                if grupo not in groups_cache:
                    existing_group = db.query(AccountGroup).filter(
                        AccountGroup.name == grupo,
                        AccountGroup.tenant_id == tenant.id,
                        AccountGroup.business_unit_id == business_unit.id
                    ).first()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group_id = str(uuid4())
                        new_group = AccountGroup(
                            id=group_id,
                            name=grupo,
                            code=grupo[:10].upper(),
                            description=f"Grupo: {grupo}",
                            tenant_id=tenant.id,
                            business_unit_id=business_unit.id,
                            status="active"
                        )
                        db.add(new_group)
                        groups_cache[grupo] = new_group
                        groups_created += 1
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_obj = groups_cache[grupo]
                
                # 2. Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    existing_subgroup = db.query(AccountSubgroup).filter(
                        AccountSubgroup.name == subgrupo,
                        AccountSubgroup.group_id == groups_cache[grupo].id,
                        AccountSubgroup.tenant_id == tenant.id,
                        AccountSubgroup.business_unit_id == business_unit.id
                    ).first()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup_id = str(uuid4())
                        new_subgroup = AccountSubgroup(
                            id=subgroup_id,
                            name=subgrupo,
                            code=subgrupo[:10].upper(),
                            description=f"Subgrupo: {subgrupo}",
                            group_id=groups_cache[grupo].id,
                            tenant_id=tenant.id,
                            business_unit_id=business_unit.id,
                            status="active"
                        )
                        db.add(new_subgroup)
                        subgroups_cache[subgroup_key] = new_subgroup
                        subgroups_created += 1
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_obj = subgroups_cache[subgroup_key]
                
                # 3. Criar conta
                existing_account = db.query(ChartAccount).filter(
                    ChartAccount.name == conta,
                    ChartAccount.subgroup_id == subgroups_cache[subgroup_key].id,
                    ChartAccount.tenant_id == tenant.id,
                    ChartAccount.business_unit_id == business_unit.id
                ).first()
                
                if not existing_account:
                    account_id = str(uuid4())
                    new_account = ChartAccount(
                        id=account_id,
                        name=conta,
                        code=conta[:10].upper(),
                        description=f"Conta: {conta}",
                        subgroup_id=subgroups_cache[subgroup_key].id,
                        tenant_id=tenant.id,
                        business_unit_id=business_unit.id,
                        is_active=is_active,
                        status="active"
                    )
                    db.add(new_account)
                    accounts_created += 1
                    print(f"✅ Conta criada: {conta} ({'Ativa' if is_active else 'Inativa'})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        # Commit das mudanças
        db.commit()
        print("🎉 Importação concluída com sucesso!")
        
        # Estatísticas finais
        print(f"📊 Estatísticas:")
        print(f"   - Grupos criados: {groups_created}")
        print(f"   - Subgrupos criados: {subgroups_created}")
        print(f"   - Contas criadas: {accounts_created}")
        
        # Contar total no banco
        total_groups = db.query(AccountGroup).filter(
            AccountGroup.tenant_id == tenant.id,
            AccountGroup.business_unit_id == business_unit.id
        ).count()
        
        total_subgroups = db.query(AccountSubgroup).filter(
            AccountSubgroup.tenant_id == tenant.id,
            AccountSubgroup.business_unit_id == business_unit.id
        ).count()
        
        total_accounts = db.query(ChartAccount).filter(
            ChartAccount.tenant_id == tenant.id,
            ChartAccount.business_unit_id == business_unit.id
        ).count()
        
        print(f"📊 Total no banco:")
        print(f"   - Grupos: {total_groups}")
        print(f"   - Subgrupos: {total_subgroups}")
        print(f"   - Contas: {total_accounts}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = import_chart_of_accounts()
    if success:
        print("✅ Importação finalizada com sucesso!")
    else:
        print("❌ Importação falhou!")
        sys.exit(1)
