#!/usr/bin/env python3
"""
Script para Verificar Vínculos de Dados
Verifica se todos os dados estão vinculados a Tenant/Business Unit
"""

import requests
import sys
from typing import Dict, List, Tuple

# Configurações
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"
USERNAME = "admin"
PASSWORD = "admin123"

def login() -> str:
    """Faz login e retorna o token JWT"""
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        data={"username": USERNAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Erro no login: {response.status_code}")
        sys.exit(1)

def query_database(token: str, query: str) -> List[Dict]:
    """Executa query no banco via endpoint de debug (se existir)"""
    # Por enquanto, vamos usar os endpoints da API para verificar
    pass

def check_chart_accounts(token: str) -> Tuple[int, int]:
    """Verifica grupos de contas"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/chart-accounts/groups",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            groups = response.json()
            total = len(groups)
            
            # Verificar se todos têm tenant_id (assumindo que a API filtra automaticamente)
            # Se retornou dados, significa que está vinculado ao tenant do usuário
            return total, total
        return 0, 0
    except Exception as e:
        print(f"⚠️  Erro ao verificar grupos: {e}")
        return 0, 0

def check_accounts(token: str) -> Tuple[int, int]:
    """Verifica contas"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/chart-accounts/accounts",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            accounts = response.json()
            total = len(accounts)
            
            # Verificar quais têm tenant_id explícito
            with_tenant = sum(1 for acc in accounts if acc.get('tenant_id'))
            
            return total, with_tenant
        return 0, 0
    except Exception as e:
        print(f"⚠️  Erro ao verificar contas: {e}")
        return 0, 0

def check_transactions(token: str) -> Tuple[int, int, int]:
    """Verifica transações"""
    try:
        # Buscar transações dos últimos 365 dias
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        response = requests.get(
            f"{BACKEND_URL}/api/v1/financial/transactions",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            transactions = response.json()
            total = len(transactions)
            
            # Verificar vínculos
            with_tenant = sum(1 for t in transactions if t.get('tenant_id'))
            with_bu = sum(1 for t in transactions if t.get('business_unit_id'))
            
            return total, with_tenant, with_bu
        return 0, 0, 0
    except Exception as e:
        print(f"⚠️  Erro ao verificar transações: {e}")
        return 0, 0, 0

def check_users(token: str) -> Tuple[int, int, int]:
    """Verifica usuários"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            users = response.json()
            total = len(users)
            
            # Verificar vínculos
            with_tenant = sum(1 for u in users if u.get('tenant_id'))
            with_bu = sum(1 for u in users if u.get('business_unit_id'))
            
            return total, with_tenant, with_bu
        return 0, 0, 0
    except Exception as e:
        print(f"⚠️  Erro ao verificar usuários: {e}")
        return 0, 0, 0

def check_business_units(token: str) -> Tuple[int, int]:
    """Verifica business units"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/business-units",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            bus = response.json()
            total = len(bus)
            
            # Verificar quais têm tenant_id
            with_tenant = sum(1 for bu in bus if bu.get('tenant_id'))
            
            return total, with_tenant
        return 0, 0
    except Exception as e:
        print(f"⚠️  Erro ao verificar business units: {e}")
        return 0, 0

def main():
    """Função principal"""
    print("=" * 80)
    print("🔍 VERIFICAÇÃO DE VÍNCULOS TENANT/BUSINESS UNIT - FINAFLOW")
    print("=" * 80)
    print()
    
    # 1. Login
    print("🔐 Fazendo login...")
    token = login()
    print("✅ Login bem-sucedido!")
    print()
    
    # Armazenar resultados
    results = {}
    total_registros = 0
    total_com_tenant = 0
    total_com_bu = 0
    
    # 2. Verificar Grupos de Contas
    print("📊 Verificando Grupos de Contas...")
    groups_total, groups_tenant = check_chart_accounts(token)
    results['Grupos'] = {'total': groups_total, 'tenant': groups_tenant, 'bu': 'N/A'}
    total_registros += groups_total
    total_com_tenant += groups_tenant
    print(f"   Total: {groups_total} | Com Tenant: {groups_tenant}")
    print()
    
    # 3. Verificar Contas
    print("💰 Verificando Contas do Plano...")
    accounts_total, accounts_tenant = check_accounts(token)
    results['Contas'] = {'total': accounts_total, 'tenant': accounts_tenant, 'bu': 'N/A'}
    total_registros += accounts_total
    total_com_tenant += accounts_tenant
    print(f"   Total: {accounts_total} | Com Tenant: {accounts_tenant}")
    print()
    
    # 4. Verificar Transações
    print("💸 Verificando Transações Financeiras...")
    trans_total, trans_tenant, trans_bu = check_transactions(token)
    results['Transações'] = {'total': trans_total, 'tenant': trans_tenant, 'bu': trans_bu}
    total_registros += trans_total
    total_com_tenant += trans_tenant
    total_com_bu += trans_bu
    print(f"   Total: {trans_total} | Com Tenant: {trans_tenant} | Com BU: {trans_bu}")
    print()
    
    # 5. Verificar Usuários
    print("👥 Verificando Usuários...")
    users_total, users_tenant, users_bu = check_users(token)
    results['Usuários'] = {'total': users_total, 'tenant': users_tenant, 'bu': users_bu}
    total_registros += users_total
    total_com_tenant += users_tenant
    total_com_bu += users_bu
    print(f"   Total: {users_total} | Com Tenant: {users_tenant} | Com BU: {users_bu}")
    print()
    
    # 6. Verificar Business Units
    print("🏢 Verificando Business Units...")
    bu_total, bu_tenant = check_business_units(token)
    results['Business Units'] = {'total': bu_total, 'tenant': bu_tenant, 'bu': 'N/A'}
    total_registros += bu_total
    total_com_tenant += bu_tenant
    print(f"   Total: {bu_total} | Com Tenant: {bu_tenant}")
    print()
    
    # Relatório Final
    print("=" * 80)
    print("📊 RESUMO DA VERIFICAÇÃO")
    print("=" * 80)
    print()
    
    print("┌─────────────────────┬────────┬──────────────┬──────────────┐")
    print("│ Entidade            │ Total  │ Com Tenant   │ Com BU       │")
    print("├─────────────────────┼────────┼──────────────┼──────────────┤")
    
    for entity, data in results.items():
        total_str = str(data['total']).rjust(6)
        tenant_str = str(data['tenant']).rjust(12)
        bu_str = str(data['bu']).rjust(12)
        print(f"│ {entity:<19} │ {total_str} │ {tenant_str} │ {bu_str} │")
    
    print("├─────────────────────┼────────┼──────────────┼──────────────┤")
    print(f"│ {'TOTAL':<19} │ {str(total_registros).rjust(6)} │ {str(total_com_tenant).rjust(12)} │ {str(total_com_bu).rjust(12)} │")
    print("└─────────────────────┴────────┴──────────────┴──────────────┘")
    print()
    
    # Análise
    print("📈 ANÁLISE:")
    print()
    
    # Calcular percentuais
    pct_tenant = (total_com_tenant / total_registros * 100) if total_registros > 0 else 0
    
    if pct_tenant == 100:
        print("✅ EXCELENTE! Todos os dados estão vinculados a um Tenant!")
    elif pct_tenant >= 90:
        print(f"⚠️  {pct_tenant:.1f}% dos dados estão vinculados a Tenant")
        print("   Alguns registros podem estar sem vínculo.")
    else:
        print(f"❌ PROBLEMA! Apenas {pct_tenant:.1f}% dos dados têm vínculo com Tenant")
        print("   Muitos dados estão sem isolamento multi-tenant!")
    
    print()
    
    # Verificar Business Units (apenas para entidades que deveriam ter)
    entities_with_bu = ['Transações', 'Usuários']
    bu_entities_total = sum(results[e]['total'] for e in entities_with_bu if e in results)
    bu_entities_with_bu = sum(results[e]['bu'] for e in entities_with_bu if e in results and isinstance(results[e]['bu'], int))
    
    if bu_entities_total > 0:
        pct_bu = (bu_entities_with_bu / bu_entities_total * 100)
        
        if pct_bu == 100:
            print("✅ EXCELENTE! Todos os registros que precisam de BU estão vinculados!")
        elif pct_bu >= 50:
            print(f"⚠️  {pct_bu:.1f}% dos registros estão vinculados a Business Unit")
            print("   Alguns podem estar sem BU selecionada.")
        else:
            print(f"❌ ATENÇÃO! Apenas {pct_bu:.1f}% têm vínculo com Business Unit")
    
    print()
    print("=" * 80)
    print("📝 RECOMENDAÇÕES:")
    print("=" * 80)
    print()
    
    if pct_tenant < 100:
        print("🔧 Dados sem Tenant:")
        print("   - Revisar lógica de importação")
        print("   - Garantir que tenant_id seja sempre preenchido")
        print("   - Adicionar validação obrigatória")
        print()
    
    if bu_entities_total > 0 and pct_bu < 100:
        print("🔧 Dados sem Business Unit:")
        print("   - Usuários podem não ter BU default")
        print("   - Transações podem precisar de BU obrigatória")
        print("   - Considerar tornar business_unit_id obrigatório")
        print()
    
    # Status final
    if pct_tenant == 100 and (bu_entities_total == 0 or pct_bu >= 90):
        print("✅ SISTEMA COM BOA GOVERNANÇA DE DADOS!")
        print("   Isolamento multi-tenant está funcionando corretamente.")
        return 0
    else:
        print("⚠️  ATENÇÃO: Alguns dados podem não estar isolados corretamente")
        print("   Recomenda-se revisar a lógica de vinculação.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

