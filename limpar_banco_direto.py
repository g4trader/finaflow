#!/usr/bin/env python3
"""
🗑️ LIMPEZA DIRETA NO BANCO DE DADOS
Conectar direto ao PostgreSQL e limpar dados de teste
"""

import psycopg2
import requests

# Configurações do banco (via Cloud SQL Proxy ou direto)
DB_CONFIG = {
    "host": "/cloudsql/trivihair:us-central1:finaflow-db",  # Unix socket
    "database": "finaflow_db",
    "user": "finaflow_user",
    "password": "finaflow_password"
}

# Obter tenant_id e business_unit_id do usuário
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"
CREDENTIALS = {"username": "lucianoterresrosa", "password": "xs95LIa9ZduX"}

print("🎯 LIMPEZA DIRETA NO BANCO DE DADOS")
print("=" * 60)

# Login para obter IDs
print("🔐 Fazendo login...")
response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=10)
token = response.json()["access_token"]

# Decodificar token para obter IDs
import jwt
decoded_token = jwt.decode(token, options={"verify_signature": False})
tenant_id = decoded_token["tenant_id"]
business_unit_id = decoded_token["business_unit_id"]

print(f"✅ Tenant ID: {tenant_id}")
print(f"✅ Business Unit ID: {business_unit_id}")

# Tentar conexão com Cloud SQL via Unix Socket
print("\n🔌 Tentando conectar ao banco de dados...")

try:
    # Tentar Unix socket primeiro (se estiver em ambiente GCP)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conectado via Unix socket")
    except:
        # Tentar TCP se Unix socket falhar
        DB_CONFIG_TCP = {
            "host": "localhost",  # Assumindo Cloud SQL Proxy rodando local
            "port": 5432,
            "database": "finaflow_db",
            "user": "finaflow_user",
            "password": "finaflow_password"
        }
        conn = psycopg2.connect(**DB_CONFIG_TCP)
        print("✅ Conectado via TCP")
    
    cursor = conn.cursor()
    
    # Contar lançamentos antes
    cursor.execute("""
        SELECT COUNT(*) FROM lancamentos_diarios 
        WHERE tenant_id = %s AND business_unit_id = %s
    """, (tenant_id, business_unit_id))
    count_before = cursor.fetchone()[0]
    print(f"\n📊 Lançamentos ANTES: {count_before}")
    
    if count_before > 0:
        # Deletar lançamentos
        print(f"\n🗑️ Removendo {count_before} lançamentos...")
        cursor.execute("""
            DELETE FROM lancamentos_diarios 
            WHERE tenant_id = %s AND business_unit_id = %s
        """, (tenant_id, business_unit_id))
        
        # Commit
        conn.commit()
        
        # Contar após
        cursor.execute("""
            SELECT COUNT(*) FROM lancamentos_diarios 
            WHERE tenant_id = %s AND business_unit_id = %s
        """, (tenant_id, business_unit_id))
        count_after = cursor.fetchone()[0]
        print(f"📊 Lançamentos DEPOIS: {count_after}")
        
        if count_after == 0:
            print("\n🎉 SUCESSO TOTAL!")
            print("✅ Sistema completamente limpo")
            print("✅ Todos os dados de teste removidos")
            print("✅ Pronto para importar dados reais")
        else:
            print(f"\n⚠️ Ainda há {count_after} lançamentos")
    else:
        print("\n✅ Nenhum lançamento para remover")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Erro ao conectar ao banco: {str(e)}")
    print("\n💡 SOLUÇÃO ALTERNATIVA:")
    print("Execute manualmente no GCP Cloud SQL:")
    print(f"""
    DELETE FROM lancamentos_diarios 
    WHERE tenant_id = '{tenant_id}' 
    AND business_unit_id = '{business_unit_id}';
    """)

print("=" * 60)

