#!/usr/bin/env python3
import csv
import os
import psycopg2
from uuid import uuid4
from datetime import datetime

# Configuração do banco de dados
DB_CONFIG = {
    "host": "34.70.102.98",
    "database": "finaflow_db",
    "user": "finaflow_user",
    "password": "finaflow123"
}

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu(cursor):
    """Obtém ou cria o tenant e business unit padrão"""
    
    # Buscar tenant padrão
    cursor.execute("SELECT id, name FROM tenants LIMIT 1")
    tenant_result = cursor.fetchone()
    
    if not tenant_result:
        # Criar tenant padrão
        tenant_id = str(uuid4())
        cursor.execute(
            "INSERT INTO tenants (id, name, code, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant_id, "Empresa Padrão", "EMP001", "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Tenant criado: Empresa Padrão")
    else:
        tenant_id = tenant_result[0]
        print(f"�� Tenant existente: {tenant_result[1]}")
    
    # Buscar business unit padrão
    cursor.execute("SELECT id, name FROM business_units WHERE tenant_id = %s LIMIT 1", (tenant_id,))
    bu_result = cursor.fetchone()
    
    if not bu_result:
        # Criar business unit padrão
        bu_id = str(uuid4())
        cursor.execute(
            "INSERT INTO business_units (id, name, code, tenant_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (bu_id, "BU Principal", "BU001", tenant_id, "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Business Unit criado: BU Principal")
    else:
        bu_id = bu_result[0]
        print(f"🏢 Business Unit existente: {bu_result[1]}")
    
    return tenant_id, bu_id

def import_csv_data():
    print("🚀 Iniciando importação direta no PostgreSQL...")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Obter tenant e BU
        tenant_id, bu_id = get_or_create_tenant_and_bu(cursor)
        print(f"📋 Usando Tenant ID: {tenant_id}")
        print(f"🏢 Usando Business Unit ID: {bu_id}")
        
        # Cache para grupos e subgrupos
        groups_cache = {}
        subgroups_cache = {}
        
        if not os.path.exists(CSV_FILE):
            print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
            return
        
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
                    cursor.execute(
                        "SELECT id FROM account_groups WHERE name = %s AND tenant_id = %s AND business_unit_id = %s",
                        (grupo, tenant_id, bu_id)
                    )
                    existing_group = cursor.fetchone()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group[0]
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_groups (id, name, code, description, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (group_id, grupo, grupo[:10].upper(), f"Grupo: {grupo}", tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        groups_cache[grupo] = group_id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    cursor.execute(
                        "SELECT id FROM account_subgroups WHERE name = %s AND group_id = %s AND tenant_id = %s AND business_unit_id = %s",
                        (subgrupo, groups_cache[grupo], tenant_id, bu_id)
                    )
                    existing_subgroup = cursor.fetchone()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup[0]
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_subgroups (id, name, code, description, group_id, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (subgroup_id, subgrupo, subgrupo[:10].upper(), f"Subgrupo: {subgrupo}", groups_cache[grupo], tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        subgroups_cache[subgroup_key] = subgroup_id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                cursor.execute(
                    "SELECT id FROM chart_accounts WHERE name = %s AND subgroup_id = %s AND tenant_id = %s AND business_unit_id = %s",
                    (conta, subgroups_cache[subgroup_key], tenant_id, bu_id)
                )
                existing_account = cursor.fetchone()
                
                if not existing_account:
                    account_id = str(uuid4())
                    cursor.execute(
                        "INSERT INTO chart_accounts (id, name, code, description, subgroup_id, tenant_id, business_unit_id, is_active, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (account_id, conta, conta[:10].upper(), f"Conta: {conta}", subgroups_cache[subgroup_key], tenant_id, bu_id, is_active, "active", datetime.utcnow(), datetime.utcnow())
                    )
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        # Commit das mudanças
        conn.commit()
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        if "conn" in locals():
            conn.rollback()
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()

if __name__ == "__main__":
    import_csv_data()

import os
import psycopg2
from uuid import uuid4
from datetime import datetime

# Configuração do banco de dados
DB_CONFIG = {
    "host": "34.70.102.98",
    "database": "finaflow_db",
    "user": "finaflow_user",
    "password": "finaflow123"
}

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu(cursor):
    """Obtém ou cria o tenant e business unit padrão"""
    
    # Buscar tenant padrão
    cursor.execute("SELECT id, name FROM tenants LIMIT 1")
    tenant_result = cursor.fetchone()
    
    if not tenant_result:
        # Criar tenant padrão
        tenant_id = str(uuid4())
        cursor.execute(
            "INSERT INTO tenants (id, name, code, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant_id, "Empresa Padrão", "EMP001", "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Tenant criado: Empresa Padrão")
    else:
        tenant_id = tenant_result[0]
        print(f"�� Tenant existente: {tenant_result[1]}")
    
    # Buscar business unit padrão
    cursor.execute("SELECT id, name FROM business_units WHERE tenant_id = %s LIMIT 1", (tenant_id,))
    bu_result = cursor.fetchone()
    
    if not bu_result:
        # Criar business unit padrão
        bu_id = str(uuid4())
        cursor.execute(
            "INSERT INTO business_units (id, name, code, tenant_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (bu_id, "BU Principal", "BU001", tenant_id, "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Business Unit criado: BU Principal")
    else:
        bu_id = bu_result[0]
        print(f"🏢 Business Unit existente: {bu_result[1]}")
    
    return tenant_id, bu_id

def import_csv_data():
    print("🚀 Iniciando importação direta no PostgreSQL...")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Obter tenant e BU
        tenant_id, bu_id = get_or_create_tenant_and_bu(cursor)
        print(f"📋 Usando Tenant ID: {tenant_id}")
        print(f"🏢 Usando Business Unit ID: {bu_id}")
        
        # Cache para grupos e subgrupos
        groups_cache = {}
        subgroups_cache = {}
        
        if not os.path.exists(CSV_FILE):
            print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
            return
        
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
                    cursor.execute(
                        "SELECT id FROM account_groups WHERE name = %s AND tenant_id = %s AND business_unit_id = %s",
                        (grupo, tenant_id, bu_id)
                    )
                    existing_group = cursor.fetchone()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group[0]
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_groups (id, name, code, description, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (group_id, grupo, grupo[:10].upper(), f"Grupo: {grupo}", tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        groups_cache[grupo] = group_id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    cursor.execute(
                        "SELECT id FROM account_subgroups WHERE name = %s AND group_id = %s AND tenant_id = %s AND business_unit_id = %s",
                        (subgrupo, groups_cache[grupo], tenant_id, bu_id)
                    )
                    existing_subgroup = cursor.fetchone()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup[0]
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_subgroups (id, name, code, description, group_id, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (subgroup_id, subgrupo, subgrupo[:10].upper(), f"Subgrupo: {subgrupo}", groups_cache[grupo], tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        subgroups_cache[subgroup_key] = subgroup_id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                cursor.execute(
                    "SELECT id FROM chart_accounts WHERE name = %s AND subgroup_id = %s AND tenant_id = %s AND business_unit_id = %s",
                    (conta, subgroups_cache[subgroup_key], tenant_id, bu_id)
                )
                existing_account = cursor.fetchone()
                
                if not existing_account:
                    account_id = str(uuid4())
                    cursor.execute(
                        "INSERT INTO chart_accounts (id, name, code, description, subgroup_id, tenant_id, business_unit_id, is_active, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (account_id, conta, conta[:10].upper(), f"Conta: {conta}", subgroups_cache[subgroup_key], tenant_id, bu_id, is_active, "active", datetime.utcnow(), datetime.utcnow())
                    )
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        # Commit das mudanças
        conn.commit()
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        if "conn" in locals():
            conn.rollback()
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()

if __name__ == "__main__":
    import_csv_data()

import os
import psycopg2
from uuid import uuid4
from datetime import datetime

# Configuração do banco de dados
DB_CONFIG = {
    "host": "34.70.102.98",
    "database": "finaflow_db",
    "user": "finaflow_user",
    "password": "finaflow123"
}

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu(cursor):
    """Obtém ou cria o tenant e business unit padrão"""
    
    # Buscar tenant padrão
    cursor.execute("SELECT id, name FROM tenants LIMIT 1")
    tenant_result = cursor.fetchone()
    
    if not tenant_result:
        # Criar tenant padrão
        tenant_id = str(uuid4())
        cursor.execute(
            "INSERT INTO tenants (id, name, code, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant_id, "Empresa Padrão", "EMP001", "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Tenant criado: Empresa Padrão")
    else:
        tenant_id = tenant_result[0]
        print(f"�� Tenant existente: {tenant_result[1]}")
    
    # Buscar business unit padrão
    cursor.execute("SELECT id, name FROM business_units WHERE tenant_id = %s LIMIT 1", (tenant_id,))
    bu_result = cursor.fetchone()
    
    if not bu_result:
        # Criar business unit padrão
        bu_id = str(uuid4())
        cursor.execute(
            "INSERT INTO business_units (id, name, code, tenant_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (bu_id, "BU Principal", "BU001", tenant_id, "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Business Unit criado: BU Principal")
    else:
        bu_id = bu_result[0]
        print(f"🏢 Business Unit existente: {bu_result[1]}")
    
    return tenant_id, bu_id

def import_csv_data():
    print("🚀 Iniciando importação direta no PostgreSQL...")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Obter tenant e BU
        tenant_id, bu_id = get_or_create_tenant_and_bu(cursor)
        print(f"📋 Usando Tenant ID: {tenant_id}")
        print(f"🏢 Usando Business Unit ID: {bu_id}")
        
        # Cache para grupos e subgrupos
        groups_cache = {}
        subgroups_cache = {}
        
        if not os.path.exists(CSV_FILE):
            print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
            return
        
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
                    cursor.execute(
                        "SELECT id FROM account_groups WHERE name = %s AND tenant_id = %s AND business_unit_id = %s",
                        (grupo, tenant_id, bu_id)
                    )
                    existing_group = cursor.fetchone()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group[0]
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_groups (id, name, code, description, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (group_id, grupo, grupo[:10].upper(), f"Grupo: {grupo}", tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        groups_cache[grupo] = group_id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    cursor.execute(
                        "SELECT id FROM account_subgroups WHERE name = %s AND group_id = %s AND tenant_id = %s AND business_unit_id = %s",
                        (subgrupo, groups_cache[grupo], tenant_id, bu_id)
                    )
                    existing_subgroup = cursor.fetchone()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup[0]
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_subgroups (id, name, code, description, group_id, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (subgroup_id, subgrupo, subgrupo[:10].upper(), f"Subgrupo: {subgrupo}", groups_cache[grupo], tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        subgroups_cache[subgroup_key] = subgroup_id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                cursor.execute(
                    "SELECT id FROM chart_accounts WHERE name = %s AND subgroup_id = %s AND tenant_id = %s AND business_unit_id = %s",
                    (conta, subgroups_cache[subgroup_key], tenant_id, bu_id)
                )
                existing_account = cursor.fetchone()
                
                if not existing_account:
                    account_id = str(uuid4())
                    cursor.execute(
                        "INSERT INTO chart_accounts (id, name, code, description, subgroup_id, tenant_id, business_unit_id, is_active, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (account_id, conta, conta[:10].upper(), f"Conta: {conta}", subgroups_cache[subgroup_key], tenant_id, bu_id, is_active, "active", datetime.utcnow(), datetime.utcnow())
                    )
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        # Commit das mudanças
        conn.commit()
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        if "conn" in locals():
            conn.rollback()
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()

if __name__ == "__main__":
    import_csv_data()

import os
import psycopg2
from uuid import uuid4
from datetime import datetime

# Configuração do banco de dados
DB_CONFIG = {
    "host": "34.70.102.98",
    "database": "finaflow_db",
    "user": "finaflow_user",
    "password": "finaflow123"
}

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu(cursor):
    """Obtém ou cria o tenant e business unit padrão"""
    
    # Buscar tenant padrão
    cursor.execute("SELECT id, name FROM tenants LIMIT 1")
    tenant_result = cursor.fetchone()
    
    if not tenant_result:
        # Criar tenant padrão
        tenant_id = str(uuid4())
        cursor.execute(
            "INSERT INTO tenants (id, name, code, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant_id, "Empresa Padrão", "EMP001", "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Tenant criado: Empresa Padrão")
    else:
        tenant_id = tenant_result[0]
        print(f"�� Tenant existente: {tenant_result[1]}")
    
    # Buscar business unit padrão
    cursor.execute("SELECT id, name FROM business_units WHERE tenant_id = %s LIMIT 1", (tenant_id,))
    bu_result = cursor.fetchone()
    
    if not bu_result:
        # Criar business unit padrão
        bu_id = str(uuid4())
        cursor.execute(
            "INSERT INTO business_units (id, name, code, tenant_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (bu_id, "BU Principal", "BU001", tenant_id, "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Business Unit criado: BU Principal")
    else:
        bu_id = bu_result[0]
        print(f"🏢 Business Unit existente: {bu_result[1]}")
    
    return tenant_id, bu_id

def import_csv_data():
    print("🚀 Iniciando importação direta no PostgreSQL...")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Obter tenant e BU
        tenant_id, bu_id = get_or_create_tenant_and_bu(cursor)
        print(f"📋 Usando Tenant ID: {tenant_id}")
        print(f"🏢 Usando Business Unit ID: {bu_id}")
        
        # Cache para grupos e subgrupos
        groups_cache = {}
        subgroups_cache = {}
        
        if not os.path.exists(CSV_FILE):
            print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
            return
        
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
                    cursor.execute(
                        "SELECT id FROM account_groups WHERE name = %s AND tenant_id = %s AND business_unit_id = %s",
                        (grupo, tenant_id, bu_id)
                    )
                    existing_group = cursor.fetchone()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group[0]
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_groups (id, name, code, description, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (group_id, grupo, grupo[:10].upper(), f"Grupo: {grupo}", tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        groups_cache[grupo] = group_id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    cursor.execute(
                        "SELECT id FROM account_subgroups WHERE name = %s AND group_id = %s AND tenant_id = %s AND business_unit_id = %s",
                        (subgrupo, groups_cache[grupo], tenant_id, bu_id)
                    )
                    existing_subgroup = cursor.fetchone()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup[0]
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_subgroups (id, name, code, description, group_id, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (subgroup_id, subgrupo, subgrupo[:10].upper(), f"Subgrupo: {subgrupo}", groups_cache[grupo], tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        subgroups_cache[subgroup_key] = subgroup_id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                cursor.execute(
                    "SELECT id FROM chart_accounts WHERE name = %s AND subgroup_id = %s AND tenant_id = %s AND business_unit_id = %s",
                    (conta, subgroups_cache[subgroup_key], tenant_id, bu_id)
                )
                existing_account = cursor.fetchone()
                
                if not existing_account:
                    account_id = str(uuid4())
                    cursor.execute(
                        "INSERT INTO chart_accounts (id, name, code, description, subgroup_id, tenant_id, business_unit_id, is_active, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (account_id, conta, conta[:10].upper(), f"Conta: {conta}", subgroups_cache[subgroup_key], tenant_id, bu_id, is_active, "active", datetime.utcnow(), datetime.utcnow())
                    )
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        # Commit das mudanças
        conn.commit()
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        if "conn" in locals():
            conn.rollback()
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()

if __name__ == "__main__":
    import_csv_data()

import os
import psycopg2
from uuid import uuid4
from datetime import datetime

# Configuração do banco de dados
DB_CONFIG = {
    "host": "34.70.102.98",
    "database": "finaflow_db",
    "user": "finaflow_user",
    "password": "finaflow123"
}

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def get_or_create_tenant_and_bu(cursor):
    """Obtém ou cria o tenant e business unit padrão"""
    
    # Buscar tenant padrão
    cursor.execute("SELECT id, name FROM tenants LIMIT 1")
    tenant_result = cursor.fetchone()
    
    if not tenant_result:
        # Criar tenant padrão
        tenant_id = str(uuid4())
        cursor.execute(
            "INSERT INTO tenants (id, name, code, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant_id, "Empresa Padrão", "EMP001", "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Tenant criado: Empresa Padrão")
    else:
        tenant_id = tenant_result[0]
        print(f"�� Tenant existente: {tenant_result[1]}")
    
    # Buscar business unit padrão
    cursor.execute("SELECT id, name FROM business_units WHERE tenant_id = %s LIMIT 1", (tenant_id,))
    bu_result = cursor.fetchone()
    
    if not bu_result:
        # Criar business unit padrão
        bu_id = str(uuid4())
        cursor.execute(
            "INSERT INTO business_units (id, name, code, tenant_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (bu_id, "BU Principal", "BU001", tenant_id, "active", datetime.utcnow(), datetime.utcnow())
        )
        print(f"✅ Business Unit criado: BU Principal")
    else:
        bu_id = bu_result[0]
        print(f"🏢 Business Unit existente: {bu_result[1]}")
    
    return tenant_id, bu_id

def import_csv_data():
    print("🚀 Iniciando importação direta no PostgreSQL...")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Obter tenant e BU
        tenant_id, bu_id = get_or_create_tenant_and_bu(cursor)
        print(f"📋 Usando Tenant ID: {tenant_id}")
        print(f"🏢 Usando Business Unit ID: {bu_id}")
        
        # Cache para grupos e subgrupos
        groups_cache = {}
        subgroups_cache = {}
        
        if not os.path.exists(CSV_FILE):
            print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
            return
        
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
                    cursor.execute(
                        "SELECT id FROM account_groups WHERE name = %s AND tenant_id = %s AND business_unit_id = %s",
                        (grupo, tenant_id, bu_id)
                    )
                    existing_group = cursor.fetchone()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group[0]
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_groups (id, name, code, description, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (group_id, grupo, grupo[:10].upper(), f"Grupo: {grupo}", tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        groups_cache[grupo] = group_id
                        print(f"✅ Grupo criado: {grupo}")
                else:
                    group_id = groups_cache[grupo]
                
                # Criar ou obter subgrupo
                subgroup_key = f"{grupo}_{subgrupo}"
                if subgroup_key not in subgroups_cache:
                    cursor.execute(
                        "SELECT id FROM account_subgroups WHERE name = %s AND group_id = %s AND tenant_id = %s AND business_unit_id = %s",
                        (subgrupo, groups_cache[grupo], tenant_id, bu_id)
                    )
                    existing_subgroup = cursor.fetchone()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup[0]
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_subgroups (id, name, code, description, group_id, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (subgroup_id, subgrupo, subgrupo[:10].upper(), f"Subgrupo: {subgrupo}", groups_cache[grupo], tenant_id, bu_id, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        subgroups_cache[subgroup_key] = subgroup_id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                cursor.execute(
                    "SELECT id FROM chart_accounts WHERE name = %s AND subgroup_id = %s AND tenant_id = %s AND business_unit_id = %s",
                    (conta, subgroups_cache[subgroup_key], tenant_id, bu_id)
                )
                existing_account = cursor.fetchone()
                
                if not existing_account:
                    account_id = str(uuid4())
                    cursor.execute(
                        "INSERT INTO chart_accounts (id, name, code, description, subgroup_id, tenant_id, business_unit_id, is_active, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (account_id, conta, conta[:10].upper(), f"Conta: {conta}", subgroups_cache[subgroup_key], tenant_id, bu_id, is_active, "active", datetime.utcnow(), datetime.utcnow())
                    )
                    print(f"✅ Conta criada: {conta} ({Ativa if is_active else Inativa})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        # Commit das mudanças
        conn.commit()
        print("🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        if "conn" in locals():
            conn.rollback()
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()

if __name__ == "__main__":
    import_csv_data()
