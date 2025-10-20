#!/usr/bin/env python3
import csv
import os
from uuid import uuid4
from datetime import datetime

# Importar módulos do banco
from app.database import get_db
from app.models.auth import Tenant, BusinessUnit
from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu():
    """Obtém ou cria o tenant e business unit padrão"""
    db = next(get_db())
    
    # Buscar tenant padrão
    tenant = db.query(Tenant).first()
    if not tenant:
        # Criar tenant padrão
        tenant = Tenant(
            id=str(uuid4()),
            name="Empresa Padrão",
            code="EMP001",
            status="active"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"✅ Tenant criado: {tenant.name}")
    
    # Buscar business unit padrão
    bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant.id).first()
    if not bu:
        # Criar business unit padrão
        bu = BusinessUnit(
            id=str(uuid4()),
            name="BU Principal",
            code="BU001",
            tenant_id=tenant.id,
            status="active"
        )
        db.add(bu)
        db.commit()
        db.refresh(bu)
        print(f"✅ Business Unit criado: {bu.name}")
    
    db.close()
    return tenant.id, bu.id

def import_csv_data():
    print("🚀 Iniciando importação direta no banco de dados...")
    
    # Obter tenant e BU
    tenant_id, bu_id = get_or_create_tenant_and_bu()
    print(f"📋 Usando Tenant ID: {tenant_id}")
    print(f"🏢 Usando Business Unit ID: {bu_id}")
    
    # Cache para grupos e subgrupos
    groups_cache = {}
    subgroups_cache = {}
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
        return
    
    db = next(get_db())
    
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                conta = row.get("Conta", "").strip()
                subgrupo = row.get("Subgrupo", "").strip()
                grupo = row.get("Grupo", "").strip()
                escolha = row.get("Escolha", "").strip().lower()
                
                if not conta or not subgrupo or not grupo:
                    continue
                
                is_active = escolha in ["usar", "sim", "yes", "1", "true"]
                
                # Criar ou obter grupo
                if grupo not in groups_cache:
                    existing_group = db.query(AccountGroup).filter(
                        AccountGroup.name == grupo,
                        AccountGroup.tenant_id == tenant_id,
                        AccountGroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group.id
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group = AccountGroup(
                            id=str(uuid4()),
                            name=grupo,
                            code=grupo[:10].upper(),
                            description=f"Grupo: {grupo}",
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(group)
                        db.commit()
                        db.refresh(group)
                        groups_cache[grupo] = group.id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    existing_subgroup = db.query(AccountSubgroup).filter(
                        AccountSubgroup.name == subgrupo,
                        AccountSubgroup.group_id == groups_cache[grupo],
                        AccountSubgroup.tenant_id == tenant_id,
                        AccountSubgroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup.id
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup = AccountSubgroup(
                            id=str(uuid4()),
                            name=subgrupo,
                            code=subgrupo[:10].upper(),
                            description=f"Subgrupo: {subgrupo}",
                            group_id=groups_cache[grupo],
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(subgroup)
                        db.commit()
                        db.refresh(subgroup)
                        subgroups_cache[subgroup_key] = subgroup.id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                existing_account = db.query(Account).filter(
                    Account.name == conta,
                    Account.subgroup_id == subgroups_cache[subgroup_key],
                    Account.tenant_id == tenant_id,
                    Account.business_unit_id == bu_id
                ).first()
                
                if not existing_account:
                    account = Account(
                        id=str(uuid4()),
                        name=conta,
                        code=conta[:10].upper(),
                        description=f"Conta: {conta}",
                        subgroup_id=subgroups_cache[subgroup_key],
                        tenant_id=tenant_id,
                        business_unit_id=bu_id,
                        is_active=is_active,
                        status="active"
                    )
                    db.add(account)
                    db.commit()
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_data()
import csv
import os
from uuid import uuid4
from datetime import datetime

# Importar módulos do banco
from app.database import get_db
from app.models.auth import Tenant, BusinessUnit
from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu():
    """Obtém ou cria o tenant e business unit padrão"""
    db = next(get_db())
    
    # Buscar tenant padrão
    tenant = db.query(Tenant).first()
    if not tenant:
        # Criar tenant padrão
        tenant = Tenant(
            id=str(uuid4()),
            name="Empresa Padrão",
            code="EMP001",
            status="active"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"✅ Tenant criado: {tenant.name}")
    
    # Buscar business unit padrão
    bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant.id).first()
    if not bu:
        # Criar business unit padrão
        bu = BusinessUnit(
            id=str(uuid4()),
            name="BU Principal",
            code="BU001",
            tenant_id=tenant.id,
            status="active"
        )
        db.add(bu)
        db.commit()
        db.refresh(bu)
        print(f"✅ Business Unit criado: {bu.name}")
    
    db.close()
    return tenant.id, bu.id

def import_csv_data():
    print("🚀 Iniciando importação direta no banco de dados...")
    
    # Obter tenant e BU
    tenant_id, bu_id = get_or_create_tenant_and_bu()
    print(f"📋 Usando Tenant ID: {tenant_id}")
    print(f"🏢 Usando Business Unit ID: {bu_id}")
    
    # Cache para grupos e subgrupos
    groups_cache = {}
    subgroups_cache = {}
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
        return
    
    db = next(get_db())
    
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                conta = row.get("Conta", "").strip()
                subgrupo = row.get("Subgrupo", "").strip()
                grupo = row.get("Grupo", "").strip()
                escolha = row.get("Escolha", "").strip().lower()
                
                if not conta or not subgrupo or not grupo:
                    continue
                
                is_active = escolha in ["usar", "sim", "yes", "1", "true"]
                
                # Criar ou obter grupo
                if grupo not in groups_cache:
                    existing_group = db.query(AccountGroup).filter(
                        AccountGroup.name == grupo,
                        AccountGroup.tenant_id == tenant_id,
                        AccountGroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group.id
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group = AccountGroup(
                            id=str(uuid4()),
                            name=grupo,
                            code=grupo[:10].upper(),
                            description=f"Grupo: {grupo}",
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(group)
                        db.commit()
                        db.refresh(group)
                        groups_cache[grupo] = group.id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    existing_subgroup = db.query(AccountSubgroup).filter(
                        AccountSubgroup.name == subgrupo,
                        AccountSubgroup.group_id == groups_cache[grupo],
                        AccountSubgroup.tenant_id == tenant_id,
                        AccountSubgroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup.id
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup = AccountSubgroup(
                            id=str(uuid4()),
                            name=subgrupo,
                            code=subgrupo[:10].upper(),
                            description=f"Subgrupo: {subgrupo}",
                            group_id=groups_cache[grupo],
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(subgroup)
                        db.commit()
                        db.refresh(subgroup)
                        subgroups_cache[subgroup_key] = subgroup.id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                existing_account = db.query(Account).filter(
                    Account.name == conta,
                    Account.subgroup_id == subgroups_cache[subgroup_key],
                    Account.tenant_id == tenant_id,
                    Account.business_unit_id == bu_id
                ).first()
                
                if not existing_account:
                    account = Account(
                        id=str(uuid4()),
                        name=conta,
                        code=conta[:10].upper(),
                        description=f"Conta: {conta}",
                        subgroup_id=subgroups_cache[subgroup_key],
                        tenant_id=tenant_id,
                        business_unit_id=bu_id,
                        is_active=is_active,
                        status="active"
                    )
                    db.add(account)
                    db.commit()
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_data()
import csv
import os
from uuid import uuid4
from datetime import datetime

# Importar módulos do banco
from app.database import get_db
from app.models.auth import Tenant, BusinessUnit
from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu():
    """Obtém ou cria o tenant e business unit padrão"""
    db = next(get_db())
    
    # Buscar tenant padrão
    tenant = db.query(Tenant).first()
    if not tenant:
        # Criar tenant padrão
        tenant = Tenant(
            id=str(uuid4()),
            name="Empresa Padrão",
            code="EMP001",
            status="active"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"✅ Tenant criado: {tenant.name}")
    
    # Buscar business unit padrão
    bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant.id).first()
    if not bu:
        # Criar business unit padrão
        bu = BusinessUnit(
            id=str(uuid4()),
            name="BU Principal",
            code="BU001",
            tenant_id=tenant.id,
            status="active"
        )
        db.add(bu)
        db.commit()
        db.refresh(bu)
        print(f"✅ Business Unit criado: {bu.name}")
    
    db.close()
    return tenant.id, bu.id

def import_csv_data():
    print("🚀 Iniciando importação direta no banco de dados...")
    
    # Obter tenant e BU
    tenant_id, bu_id = get_or_create_tenant_and_bu()
    print(f"📋 Usando Tenant ID: {tenant_id}")
    print(f"🏢 Usando Business Unit ID: {bu_id}")
    
    # Cache para grupos e subgrupos
    groups_cache = {}
    subgroups_cache = {}
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
        return
    
    db = next(get_db())
    
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                conta = row.get("Conta", "").strip()
                subgrupo = row.get("Subgrupo", "").strip()
                grupo = row.get("Grupo", "").strip()
                escolha = row.get("Escolha", "").strip().lower()
                
                if not conta or not subgrupo or not grupo:
                    continue
                
                is_active = escolha in ["usar", "sim", "yes", "1", "true"]
                
                # Criar ou obter grupo
                if grupo not in groups_cache:
                    existing_group = db.query(AccountGroup).filter(
                        AccountGroup.name == grupo,
                        AccountGroup.tenant_id == tenant_id,
                        AccountGroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group.id
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group = AccountGroup(
                            id=str(uuid4()),
                            name=grupo,
                            code=grupo[:10].upper(),
                            description=f"Grupo: {grupo}",
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(group)
                        db.commit()
                        db.refresh(group)
                        groups_cache[grupo] = group.id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    existing_subgroup = db.query(AccountSubgroup).filter(
                        AccountSubgroup.name == subgrupo,
                        AccountSubgroup.group_id == groups_cache[grupo],
                        AccountSubgroup.tenant_id == tenant_id,
                        AccountSubgroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup.id
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup = AccountSubgroup(
                            id=str(uuid4()),
                            name=subgrupo,
                            code=subgrupo[:10].upper(),
                            description=f"Subgrupo: {subgrupo}",
                            group_id=groups_cache[grupo],
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(subgroup)
                        db.commit()
                        db.refresh(subgroup)
                        subgroups_cache[subgroup_key] = subgroup.id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                existing_account = db.query(Account).filter(
                    Account.name == conta,
                    Account.subgroup_id == subgroups_cache[subgroup_key],
                    Account.tenant_id == tenant_id,
                    Account.business_unit_id == bu_id
                ).first()
                
                if not existing_account:
                    account = Account(
                        id=str(uuid4()),
                        name=conta,
                        code=conta[:10].upper(),
                        description=f"Conta: {conta}",
                        subgroup_id=subgroups_cache[subgroup_key],
                        tenant_id=tenant_id,
                        business_unit_id=bu_id,
                        is_active=is_active,
                        status="active"
                    )
                    db.add(account)
                    db.commit()
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_data()
import csv
import os
from uuid import uuid4
from datetime import datetime

# Importar módulos do banco
from app.database import get_db
from app.models.auth import Tenant, BusinessUnit
from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu():
    """Obtém ou cria o tenant e business unit padrão"""
    db = next(get_db())
    
    # Buscar tenant padrão
    tenant = db.query(Tenant).first()
    if not tenant:
        # Criar tenant padrão
        tenant = Tenant(
            id=str(uuid4()),
            name="Empresa Padrão",
            code="EMP001",
            status="active"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"✅ Tenant criado: {tenant.name}")
    
    # Buscar business unit padrão
    bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant.id).first()
    if not bu:
        # Criar business unit padrão
        bu = BusinessUnit(
            id=str(uuid4()),
            name="BU Principal",
            code="BU001",
            tenant_id=tenant.id,
            status="active"
        )
        db.add(bu)
        db.commit()
        db.refresh(bu)
        print(f"✅ Business Unit criado: {bu.name}")
    
    db.close()
    return tenant.id, bu.id

def import_csv_data():
    print("🚀 Iniciando importação direta no banco de dados...")
    
    # Obter tenant e BU
    tenant_id, bu_id = get_or_create_tenant_and_bu()
    print(f"📋 Usando Tenant ID: {tenant_id}")
    print(f"🏢 Usando Business Unit ID: {bu_id}")
    
    # Cache para grupos e subgrupos
    groups_cache = {}
    subgroups_cache = {}
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
        return
    
    db = next(get_db())
    
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                conta = row.get("Conta", "").strip()
                subgrupo = row.get("Subgrupo", "").strip()
                grupo = row.get("Grupo", "").strip()
                escolha = row.get("Escolha", "").strip().lower()
                
                if not conta or not subgrupo or not grupo:
                    continue
                
                is_active = escolha in ["usar", "sim", "yes", "1", "true"]
                
                # Criar ou obter grupo
                if grupo not in groups_cache:
                    existing_group = db.query(AccountGroup).filter(
                        AccountGroup.name == grupo,
                        AccountGroup.tenant_id == tenant_id,
                        AccountGroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group.id
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group = AccountGroup(
                            id=str(uuid4()),
                            name=grupo,
                            code=grupo[:10].upper(),
                            description=f"Grupo: {grupo}",
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(group)
                        db.commit()
                        db.refresh(group)
                        groups_cache[grupo] = group.id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    existing_subgroup = db.query(AccountSubgroup).filter(
                        AccountSubgroup.name == subgrupo,
                        AccountSubgroup.group_id == groups_cache[grupo],
                        AccountSubgroup.tenant_id == tenant_id,
                        AccountSubgroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup.id
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup = AccountSubgroup(
                            id=str(uuid4()),
                            name=subgrupo,
                            code=subgrupo[:10].upper(),
                            description=f"Subgrupo: {subgrupo}",
                            group_id=groups_cache[grupo],
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(subgroup)
                        db.commit()
                        db.refresh(subgroup)
                        subgroups_cache[subgroup_key] = subgroup.id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                existing_account = db.query(Account).filter(
                    Account.name == conta,
                    Account.subgroup_id == subgroups_cache[subgroup_key],
                    Account.tenant_id == tenant_id,
                    Account.business_unit_id == bu_id
                ).first()
                
                if not existing_account:
                    account = Account(
                        id=str(uuid4()),
                        name=conta,
                        code=conta[:10].upper(),
                        description=f"Conta: {conta}",
                        subgroup_id=subgroups_cache[subgroup_key],
                        tenant_id=tenant_id,
                        business_unit_id=bu_id,
                        is_active=is_active,
                        status="active"
                    )
                    db.add(account)
                    db.commit()
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_data()
import csv
import os
from uuid import uuid4
from datetime import datetime

# Importar módulos do banco
from app.database import get_db
from app.models.auth import Tenant, BusinessUnit
from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu():
    """Obtém ou cria o tenant e business unit padrão"""
    db = next(get_db())
    
    # Buscar tenant padrão
    tenant = db.query(Tenant).first()
    if not tenant:
        # Criar tenant padrão
        tenant = Tenant(
            id=str(uuid4()),
            name="Empresa Padrão",
            code="EMP001",
            status="active"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"✅ Tenant criado: {tenant.name}")
    
    # Buscar business unit padrão
    bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant.id).first()
    if not bu:
        # Criar business unit padrão
        bu = BusinessUnit(
            id=str(uuid4()),
            name="BU Principal",
            code="BU001",
            tenant_id=tenant.id,
            status="active"
        )
        db.add(bu)
        db.commit()
        db.refresh(bu)
        print(f"✅ Business Unit criado: {bu.name}")
    
    db.close()
    return tenant.id, bu.id

def import_csv_data():
    print("🚀 Iniciando importação direta no banco de dados...")
    
    # Obter tenant e BU
    tenant_id, bu_id = get_or_create_tenant_and_bu()
    print(f"📋 Usando Tenant ID: {tenant_id}")
    print(f"🏢 Usando Business Unit ID: {bu_id}")
    
    # Cache para grupos e subgrupos
    groups_cache = {}
    subgroups_cache = {}
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
        return
    
    db = next(get_db())
    
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                conta = row.get("Conta", "").strip()
                subgrupo = row.get("Subgrupo", "").strip()
                grupo = row.get("Grupo", "").strip()
                escolha = row.get("Escolha", "").strip().lower()
                
                if not conta or not subgrupo or not grupo:
                    continue
                
                is_active = escolha in ["usar", "sim", "yes", "1", "true"]
                
                # Criar ou obter grupo
                if grupo not in groups_cache:
                    existing_group = db.query(AccountGroup).filter(
                        AccountGroup.name == grupo,
                        AccountGroup.tenant_id == tenant_id,
                        AccountGroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group.id
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group = AccountGroup(
                            id=str(uuid4()),
                            name=grupo,
                            code=grupo[:10].upper(),
                            description=f"Grupo: {grupo}",
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(group)
                        db.commit()
                        db.refresh(group)
                        groups_cache[grupo] = group.id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    existing_subgroup = db.query(AccountSubgroup).filter(
                        AccountSubgroup.name == subgrupo,
                        AccountSubgroup.group_id == groups_cache[grupo],
                        AccountSubgroup.tenant_id == tenant_id,
                        AccountSubgroup.business_unit_id == bu_id
                    ).first()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup.id
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup = AccountSubgroup(
                            id=str(uuid4()),
                            name=subgrupo,
                            code=subgrupo[:10].upper(),
                            description=f"Subgrupo: {subgrupo}",
                            group_id=groups_cache[grupo],
                            tenant_id=tenant_id,
                            business_unit_id=bu_id,
                            status="active"
                        )
                        db.add(subgroup)
                        db.commit()
                        db.refresh(subgroup)
                        subgroups_cache[subgroup_key] = subgroup.id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                existing_account = db.query(Account).filter(
                    Account.name == conta,
                    Account.subgroup_id == subgroups_cache[subgroup_key],
                    Account.tenant_id == tenant_id,
                    Account.business_unit_id == bu_id
                ).first()
                
                if not existing_account:
                    account = Account(
                        id=str(uuid4()),
                        name=conta,
                        code=conta[:10].upper(),
                        description=f"Conta: {conta}",
                        subgroup_id=subgroups_cache[subgroup_key],
                        tenant_id=tenant_id,
                        business_unit_id=bu_id,
                        is_active=is_active,
                        status="active"
                    )
                    db.add(account)
                    db.commit()
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_data()
