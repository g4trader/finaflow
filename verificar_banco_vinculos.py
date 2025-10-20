#!/usr/bin/env python3
"""
Verificação Direta no Banco de Dados
Conecta diretamente ao PostgreSQL para verificar vínculos
"""

import psycopg2
import sys

# Configurações do banco
DB_CONFIG = {
    'host': '34.41.169.224',
    'port': 5432,
    'database': 'finaflow_db',
    'user': 'finaflow_user',
    'password': 'finaflow_password'
}

def connect_db():
    """Conecta ao banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        sys.exit(1)

def check_table_structure(conn, table_name: str):
    """Verifica estrutura da tabela"""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        AND column_name IN ('tenant_id', 'business_unit_id')
        ORDER BY ordinal_position;
    """)
    return cursor.fetchall()

def check_data_links(conn, table_name: str):
    """Verifica vínculos nos dados"""
    cursor = conn.cursor()
    
    # Verificar se tabela existe
    cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = '{table_name}'
        );
    """)
    
    if not cursor.fetchone()[0]:
        return None, None, None, None
    
    # Contar total de registros
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    total = cursor.fetchone()[0]
    
    # Verificar coluna tenant_id
    cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = '{table_name}' AND column_name = 'tenant_id'
        );
    """)
    has_tenant_col = cursor.fetchone()[0]
    
    if has_tenant_col:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE tenant_id IS NOT NULL;")
        with_tenant = cursor.fetchone()[0]
    else:
        with_tenant = 'N/A'
    
    # Verificar coluna business_unit_id
    cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = '{table_name}' AND column_name = 'business_unit_id'
        );
    """)
    has_bu_col = cursor.fetchone()[0]
    
    if has_bu_col:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE business_unit_id IS NOT NULL;")
        with_bu = cursor.fetchone()[0]
    else:
        with_bu = 'N/A'
    
    return total, with_tenant, with_bu, has_tenant_col and has_bu_col

def main():
    print("=" * 90)
    print("🔍 VERIFICAÇÃO DIRETA NO BANCO DE DADOS - VÍNCULOS TENANT/BUSINESS UNIT")
    print("=" * 90)
    print()
    
    # Conectar ao banco
    print("🔌 Conectando ao PostgreSQL...")
    conn = connect_db()
    print("✅ Conectado com sucesso!")
    print()
    
    # Tabelas para verificar
    tables = [
        ('tenants', 'Empresas (Tenants)'),
        ('business_units', 'Filiais (Business Units)'),
        ('users', 'Usuários'),
        ('chart_account_groups', 'Grupos de Contas'),
        ('chart_account_subgroups', 'Subgrupos de Contas'),
        ('chart_accounts', 'Contas do Plano'),
        ('business_unit_chart_accounts', 'Vínculo BU-Conta'),
        ('financial_transactions', 'Transações Financeiras'),
        ('financial_forecasts', 'Previsões Financeiras'),
        ('user_business_unit_access', 'Acessos Usuário-BU'),
        ('user_tenant_access', 'Acessos Usuário-Tenant'),
    ]
    
    results = []
    
    for table_name, display_name in tables:
        print(f"📊 Verificando {display_name} ({table_name})...")
        total, with_tenant, with_bu, has_both = check_data_links(conn, table_name)
        
        if total is None:
            print(f"   ⚠️  Tabela não existe")
            results.append([display_name, 0, 'N/A', 'N/A', '❌'])
        else:
            status = '✅' if (with_tenant == total or with_tenant == 'N/A') else '⚠️'
            results.append([display_name, total, with_tenant, with_bu, status])
            print(f"   Total: {total} | Com Tenant: {with_tenant} | Com BU: {with_bu} {status}")
    
    print()
    conn.close()
    
    # Relatório Final
    print("=" * 90)
    print("📊 RESUMO COMPLETO")
    print("=" * 90)
    print()
    
    print("┌─────────────────────────────────┬────────┬──────────────┬──────────────┬────────┐")
    print("│ Entidade                        │ Total  │ Com Tenant   │ Com BU       │ Status │")
    print("├─────────────────────────────────┼────────┼──────────────┼──────────────┼────────┤")
    
    for row in results:
        entity, total, tenant, bu, status = row
        print(f"│ {entity:<31} │ {str(total).rjust(6)} │ {str(tenant).rjust(12)} │ {str(bu).rjust(12)} │ {status:^6} │")
    
    print("└─────────────────────────────────┴────────┴──────────────┴──────────────┴────────┘")
    print()
    
    # Análise detalhada
    print("=" * 90)
    print("📈 ANÁLISE DETALHADA")
    print("=" * 90)
    print()
    
    # Verificar problemas
    problemas = []
    
    for row in results:
        entity, total, tenant, bu, status = row
        
        if total == 0:
            continue
        
        # Verificar se deveria ter tenant_id
        should_have_tenant = entity not in ['Empresas (Tenants)']
        
        if should_have_tenant and tenant != 'N/A' and isinstance(tenant, int) and tenant < total:
            problemas.append(f"❌ {entity}: {total - tenant} registros SEM tenant_id")
        
        # Verificar se deveria ter business_unit_id
        should_have_bu = entity in [
            'Transações Financeiras',
            'Previsões Financeiras',
            'Vínculo BU-Conta'
        ]
        
        if should_have_bu and bu != 'N/A' and isinstance(bu, int) and bu < total:
            problemas.append(f"⚠️  {entity}: {total - bu} registros SEM business_unit_id")
    
    if problemas:
        print("🚨 PROBLEMAS ENCONTRADOS:")
        print()
        for prob in problemas:
            print(f"   {prob}")
        print()
        print("🔧 AÇÃO NECESSÁRIA:")
        print("   1. Revisar lógica de importação")
        print("   2. Adicionar tenant_id e business_unit_id obrigatórios")
        print("   3. Atualizar registros existentes sem vínculo")
        print()
        return 1
    else:
        print("✅ NENHUM PROBLEMA ENCONTRADO!")
        print()
        print("   Todos os dados estão corretamente vinculados:")
        print("   - ✅ Isolamento por Tenant (Empresa)")
        print("   - ✅ Isolamento por Business Unit (Filial)")
        print("   - ✅ Sistema multi-tenant seguro")
        print()
        return 0

if __name__ == "__main__":
    sys.exit(main())

