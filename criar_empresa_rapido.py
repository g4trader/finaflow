#!/usr/bin/env python3
"""
Script Rápido para Criar Nova Empresa
Use enquanto a interface do Vercel propaga
"""

import requests
import sys

BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"
SUPER_ADMIN_USER = "admin"
SUPER_ADMIN_PASS = "admin123"

def criar_empresa():
    print("=" * 80)
    print("🏢 CRIAR NOVA EMPRESA - FINAFLOW SAAS")
    print("=" * 80)
    print()
    
    # Pedir dados
    print("Digite os dados da nova empresa:")
    print()
    
    tenant_name = input("Nome da Empresa: ").strip()
    if not tenant_name:
        print("❌ Nome é obrigatório!")
        return
    
    tenant_domain = input("Domínio (ex: empresa.com): ").strip()
    if not tenant_domain:
        print("❌ Domínio é obrigatório!")
        return
    
    admin_email = input("Email do Admin: ").strip()
    if not admin_email:
        print("❌ Email é obrigatório!")
        return
    
    admin_first_name = input("Nome do Admin (Enter para 'Administrador'): ").strip() or "Administrador"
    admin_last_name = input("Sobrenome do Admin (Enter para nome da empresa): ").strip() or tenant_name
    
    print()
    print("=" * 80)
    print("CONFIRMAÇÃO")
    print("=" * 80)
    print(f"Empresa: {tenant_name}")
    print(f"Domínio: {tenant_domain}")
    print(f"Admin: {admin_first_name} {admin_last_name} ({admin_email})")
    print()
    
    confirm = input("Confirmar criação? (s/n): ").strip().lower()
    if confirm != 's':
        print("❌ Cancelado pelo usuário")
        return
    
    print()
    print("🔐 Fazendo login como super admin...")
    
    # Login
    login_response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        data={"username": SUPER_ADMIN_USER, "password": SUPER_ADMIN_PASS},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    print("✅ Login realizado!")
    print()
    
    # Criar empresa
    print("🏢 Criando empresa...")
    
    create_response = requests.post(
        f"{BACKEND_URL}/api/v1/admin/onboard-new-company",
        json={
            "tenant_name": tenant_name,
            "tenant_domain": tenant_domain,
            "bu_name": "Matriz",
            "bu_code": "MAT",
            "admin_email": admin_email,
            "admin_first_name": admin_first_name,
            "admin_last_name": admin_last_name,
            "import_data": False
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        timeout=60
    )
    
    if create_response.status_code != 200:
        print(f"❌ Erro ao criar empresa: {create_response.status_code}")
        try:
            error_data = create_response.json()
            print(f"Detalhes: {error_data.get('detail', error_data)}")
        except:
            print(create_response.text)
        return
    
    result = create_response.json()
    
    if not result.get("success"):
        print("❌ Erro ao criar empresa:")
        print(result.get("error", "Erro desconhecido"))
        return
    
    # Exibir resultado
    print()
    print("=" * 80)
    print("✅ EMPRESA CRIADA COM SUCESSO!")
    print("=" * 80)
    print()
    
    print("Processo executado:")
    for step in result.get("steps", []):
        print(f"  {step}")
    
    print()
    print("=" * 80)
    print("🔑 CREDENCIAIS DE ACESSO")
    print("=" * 80)
    
    company_info = result.get("company_info", {})
    
    print()
    print(f"Empresa: {company_info.get('tenant_name')}")
    print(f"Filial: {company_info.get('business_unit_name')}")
    print()
    print(f"Username: {company_info.get('admin_username')}")
    print(f"Email: {company_info.get('admin_email')}")
    print(f"Senha: {company_info.get('admin_password')}")
    print()
    print(f"URL: {company_info.get('login_url')}")
    print()
    print("=" * 80)
    print("⚠️  IMPORTANTE: SALVE ESSAS CREDENCIAIS E ENVIE PARA O CLIENTE!")
    print("=" * 80)
    print()
    
    # Próximos passos
    if result.get("next_steps"):
        print("📝 Próximos Passos:")
        print()
        for step in result["next_steps"]:
            print(f"  {step}")
        print()

if __name__ == "__main__":
    try:
        criar_empresa()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

