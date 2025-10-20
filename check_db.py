#!/usr/bin/env python3
"""Script para verificar estrutura e dados do banco"""
import psycopg2
import os
import json

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://finaflow_user:finaflow_password@34.41.169.224:5432/finaflow_db")

def parse_database_url(url):
    """Parse DATABASE_URL para componentes"""
    import re
    pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, url)
    if match:
        return {
            'user': match.group(1),
            'password': match.group(2),
            'host': match.group(3),
            'port': match.group(4),
            'database': match.group(5)
        }
    return None

try:
    db_config = parse_database_url(DATABASE_URL)
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    result = {
        "status": "success",
        "tables": {}
    }
    
    # Listar tabelas
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    
    tables = [t[0] for t in cur.fetchall()]
    
    # Para cada tabela, contar registros e pegar estrutura
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        
        # Colunas
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        
        result["tables"][table] = {
            "count": count,
            "columns": [{"name": c[0], "type": c[1]} for c in columns]
        }
    
    # Verificar dados críticos
    critical_data = {}
    
    # Usuários
    if "users" in tables:
        cur.execute("SELECT id, username, email, role FROM users ORDER BY username;")
        critical_data["users"] = [
            {"id": str(r[0]), "username": r[1], "email": r[2], "role": r[3]} 
            for r in cur.fetchall()
        ]
    
    # Tenants
    if "tenants" in tables:
        cur.execute("SELECT id, name, is_active FROM tenants ORDER BY name;")
        critical_data["tenants"] = [
            {"id": str(r[0]), "name": r[1], "is_active": r[2]} 
            for r in cur.fetchall()
        ]
    
    # Business Units
    if "business_units" in tables:
        cur.execute("SELECT id, name, tenant_id FROM business_units ORDER BY name;")
        critical_data["business_units"] = [
            {"id": str(r[0]), "name": r[1], "tenant_id": str(r[2])} 
            for r in cur.fetchall()
        ]
    
    result["critical_data"] = critical_data
    
    print(json.dumps(result, indent=2))
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}, indent=2))

