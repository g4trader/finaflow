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

# IDs conhecidos do sistema
TENANT_ID = "21564896-889d-4b5c-b431-dfa7ef4f0387"
BUSINESS_UNIT_ID = "d22ceace-80e8-4c0f-9000-88d910daaa1d"

CSV_FILE = "../csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

def import_csv_data():
    print("🚀 Iniciando importação final do plano de contas...")
    print(f"📋 Tenant ID: {TENANT_ID}")
    print(f"🏢 Business Unit ID: {BUSINESS_UNIT_ID}")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
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
                        (grupo, TENANT_ID, BUSINESS_UNIT_ID)
                    )
                    existing_group = cursor.fetchone()
                    
                    if existing_group:
                        groups_cache[grupo] = existing_group[0]
                        print(f"📁 Grupo existente: {grupo}")
                    else:
                        group_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_groups (id, name, code, description, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (group_id, grupo, grupo[:10].upper(), f"Grupo: {grupo}", TENANT_ID, BUSINESS_UNIT_ID, "active", datetime.utcnow(), datetime.utcnow())
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
                        (subgrupo, groups_cache[grupo], TENANT_ID, BUSINESS_UNIT_ID)
                    )
                    existing_subgroup = cursor.fetchone()
                    
                    if existing_subgroup:
                        subgroups_cache[subgroup_key] = existing_subgroup[0]
                        print(f"📂 Subgrupo existente: {subgrupo}")
                    else:
                        subgroup_id = str(uuid4())
                        cursor.execute(
                            "INSERT INTO account_subgroups (id, name, code, description, group_id, tenant_id, business_unit_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (subgroup_id, subgrupo, subgrupo[:10].upper(), f"Subgrupo: {subgrupo}", groups_cache[grupo], TENANT_ID, BUSINESS_UNIT_ID, "active", datetime.utcnow(), datetime.utcnow())
                        )
                        subgroups_cache[subgroup_key] = subgroup_id
                        print(f"✅ Subgrupo criado: {subgrupo}")
                else:
                    subgroup_id = subgroups_cache[subgroup_key]
                
                # Criar conta
                cursor.execute(
                    "SELECT id FROM chart_accounts WHERE name = %s AND subgroup_id = %s AND tenant_id = %s AND business_unit_id = %s",
                    (conta, subgroups_cache[subgroup_key], TENANT_ID, BUSINESS_UNIT_ID)
                )
                existing_account = cursor.fetchone()
                
                if not existing_account:
                    account_id = str(uuid4())
                    cursor.execute(
                        "INSERT INTO chart_accounts (id, name, code, description, subgroup_id, tenant_id, business_unit_id, is_active, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (account_id, conta, conta[:10].upper(), f"Conta: {conta}", subgroups_cache[subgroup_key], TENANT_ID, BUSINESS_UNIT_ID, is_active, "active", datetime.utcnow(), datetime.utcnow())
                    )
                    print(f"✅ Conta criada: {conta} ({'Ativa' if is_active else 'Inativa'})")
                else:
                    print(f"📄 Conta existente: {conta}")
        
        # Commit das mudanças
        conn.commit()
        print("🎉 Importação concluída com sucesso!")
        
        # Mostrar estatísticas finais
        cursor.execute("SELECT COUNT(*) FROM account_groups WHERE tenant_id = %s AND business_unit_id = %s", (TENANT_ID, BUSINESS_UNIT_ID))
        groups_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM account_subgroups WHERE tenant_id = %s AND business_unit_id = %s", (TENANT_ID, BUSINESS_UNIT_ID))
        subgroups_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chart_accounts WHERE tenant_id = %s AND business_unit_id = %s", (TENANT_ID, BUSINESS_UNIT_ID))
        accounts_count = cursor.fetchone()[0]
        
        print(f"📊 Estatísticas finais:")
        print(f"   - Grupos: {groups_count}")
        print(f"   - Subgrupos: {subgroups_count}")
        print(f"   - Contas: {accounts_count}")
        
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import_csv_data()



