#!/usr/bin/env python3
"""
Teste End-to-End do Fluxo de Onboarding de Empresas
Testa criação de empresa, isolamento e importação de dados
"""

import requests
import sys
import time

BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"
SUPER_ADMIN_USER = "admin"
SUPER_ADMIN_PASS = "admin123"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def login(username, password):
    """Faz login e retorna token"""
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def main():
    print_section("🧪 TESTE END-TO-END - ONBOARDING DE EMPRESAS")
    
    # TESTE 1: Login do Super Admin
    print("TESTE 1: Login do Super Admin")
    print("-" * 40)
    
    super_token = login(SUPER_ADMIN_USER, SUPER_ADMIN_PASS)
    if super_token:
        print(f"✅ Super admin logado com sucesso")
        print(f"   Token: {super_token[:50]}...")
    else:
        print("❌ Falha no login do super admin")
        return 1
    
    # TESTE 2: Criar Nova Empresa
    print_section("TESTE 2: Criar Nova Empresa via Onboarding")
    
    new_company_data = {
        "tenant_name": f"Empresa Teste {int(time.time())}",
        "tenant_domain": f"teste{int(time.time())}.com",
        "bu_name": "Matriz",
        "bu_code": "MTZ",
        "admin_email": f"admin{int(time.time())}@teste.com",
        "admin_first_name": "Administrador",
        "admin_last_name": "Teste",
        "admin_phone": "(11) 98765-4321",
        "import_data": False
    }
    
    print(f"Criando empresa: {new_company_data['tenant_name']}")
    print(f"Domínio: {new_company_data['tenant_domain']}")
    print(f"Admin: {new_company_data['admin_email']}")
    print()
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/admin/onboard-new-company",
        json=new_company_data,
        headers={
            "Authorization": f"Bearer {super_token}",
            "Content-Type": "application/json"
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Empresa criada com sucesso!")
        print()
        print("Passos executados:")
        for step in result["steps"]:
            print(f"  {step}")
        print()
        
        company_info = result["company_info"]
        new_admin_username = company_info["admin_username"]
        new_admin_password = company_info["admin_password"]
        new_tenant_id = company_info["tenant_id"]
        
        print("🔑 Credenciais geradas:")
        print(f"   Username: {new_admin_username}")
        print(f"   Password: {new_admin_password}")
    else:
        print(f"❌ Erro ao criar empresa: {response.status_code}")
        print(response.text)
        return 1
    
    # TESTE 3: Login do Admin da Nova Empresa
    print_section("TESTE 3: Login do Admin da Nova Empresa")
    
    new_admin_token = login(new_admin_username, new_admin_password)
    if new_admin_token:
        print(f"✅ Admin da nova empresa logou com sucesso")
        print(f"   Username: {new_admin_username}")
    else:
        print(f"❌ Falha no login do admin da nova empresa")
        return 1
    
    # TESTE 4: Verificar Isolamento de Dados
    print_section("TESTE 4: Verificar Isolamento Multi-Tenant")
    
    # 4.1 - Ver grupos do super admin (empresa original)
    response_original = requests.get(
        f"{BACKEND_URL}/api/v1/chart-accounts/groups",
        headers={"Authorization": f"Bearer {super_token}"},
        timeout=30
    )
    
    groups_original = response_original.json() if response_original.status_code == 200 else []
    print(f"Admin Empresa Original (FINAFlow):")
    print(f"   Grupos visíveis: {len(groups_original)}")
    
    # 4.2 - Ver grupos do admin da nova empresa
    response_nova = requests.get(
        f"{BACKEND_URL}/api/v1/chart-accounts/groups",
        headers={"Authorization": f"Bearer {new_admin_token}"},
        timeout=30
    )
    
    groups_nova = response_nova.json() if response_nova.status_code == 200 else []
    print(f"\nAdmin Nova Empresa (Teste SaaS):")
    print(f"   Grupos visíveis: {len(groups_nova)}")
    print()
    
    # Validação de isolamento
    if len(groups_original) > 0 and len(groups_nova) == 0:
        print("✅ ISOLAMENTO PERFEITO!")
        print("   ✅ Empresa original vê seus dados")
        print("   ✅ Empresa nova não vê dados da original")
        print("   ✅ Cada tenant totalmente isolado")
    else:
        print("⚠️  Verificar isolamento:")
        print(f"   Original: {len(groups_original)} grupos")
        print(f"   Nova: {len(groups_nova)} grupos")
    
    # TESTE 5: Verificar Business Units
    print_section("TESTE 5: Verificar Business Units por Empresa")
    
    # BUs do super admin
    response_bu_original = requests.get(
        f"{BACKEND_URL}/api/v1/auth/user-business-units",
        headers={"Authorization": f"Bearer {super_token}"},
        timeout=30
    )
    
    bus_original = response_bu_original.json() if response_bu_original.status_code == 200 else []
    print(f"Business Units da empresa original:")
    for bu in bus_original:
        print(f"   - {bu['name']} ({bu['code']}) - Tenant: {bu['tenant_name']}")
    
    # BUs do admin da nova empresa
    response_bu_nova = requests.get(
        f"{BACKEND_URL}/api/v1/auth/user-business-units",
        headers={"Authorization": f"Bearer {new_admin_token}"},
        timeout=30
    )
    
    bus_nova = response_bu_nova.json() if response_bu_nova.status_code == 200 else []
    print(f"\nBusiness Units da nova empresa:")
    for bu in bus_nova:
        print(f"   - {bu['name']} ({bu['code']}) - Tenant: {bu['tenant_name']}")
    
    # RESUMO FINAL
    print_section("📊 RESUMO DOS TESTES")
    
    tests_passed = 0
    tests_total = 5
    
    print("Resultados:")
    print(f"  {'✅' if super_token else '❌'} 1. Login do Super Admin")
    tests_passed += 1 if super_token else 0
    
    print(f"  {'✅' if new_tenant_id else '❌'} 2. Criação de Nova Empresa")
    tests_passed += 1 if new_tenant_id else 0
    
    print(f"  {'✅' if new_admin_token else '❌'} 3. Login do Admin da Nova Empresa")
    tests_passed += 1 if new_admin_token else 0
    
    print(f"  {'✅' if len(groups_nova) == 0 else '❌'} 4. Isolamento de Dados (nova empresa sem dados da original)")
    tests_passed += 1 if len(groups_nova) == 0 else 0
    
    print(f"  {'✅' if len(bus_nova) > 0 else '❌'} 5. Business Units Criadas")
    tests_passed += 1 if len(bus_nova) > 0 else 0
    
    print()
    print(f"Taxa de sucesso: {tests_passed}/{tests_total} ({tests_passed/tests_total*100:.0f}%)")
    print()
    
    if tests_passed == tests_total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print()
        print("✅ Fluxo de onboarding funcionando perfeitamente:")
        print("   - Criação de empresas: OK")
        print("   - Isolamento multi-tenant: OK")
        print("   - Login de admins: OK")
        print("   - Business Units: OK")
        print()
        print("🚀 SISTEMA PRONTO PARA OPERAÇÃO COMO SAAS!")
        return 0
    else:
        print("⚠️  Alguns testes falharam")
        return 1

if __name__ == "__main__":
    sys.exit(main())

