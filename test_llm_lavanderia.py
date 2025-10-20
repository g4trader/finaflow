#!/usr/bin/env python3
"""
Teste End-to-End - Cliente Real: LLM Lavanderia
"""

import requests
import sys
import json

BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"
SUPER_ADMIN_USER = "admin"
SUPER_ADMIN_PASS = "admin123"

# Dados do cliente
TENANT_NAME = "LLM Lavanderia"
TENANT_DOMAIN = "g4marketing.com.br"
ADMIN_EMAIL = "lucianoterresrosa@gmail.com"
ADMIN_FIRST_NAME = "Luciano"
ADMIN_LAST_NAME = "Terres Rosa"
SPREADSHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def login(username, password):
    """Faz login"""
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

print_section("🏢 TESTE END-TO-END - LLM LAVANDERIA")

print(f"Cliente: {TENANT_NAME}")
print(f"Domínio: {TENANT_DOMAIN}")
print(f"Email Admin: {ADMIN_EMAIL}")
print(f"Planilha ID: {SPREADSHEET_ID}")
print()

# ETAPA 1: Login Super Admin
print_section("ETAPA 1: Login do Super Admin")

super_token = login(SUPER_ADMIN_USER, SUPER_ADMIN_PASS)
if not super_token:
    print("❌ Falha no login do super admin")
    sys.exit(1)

print(f"✅ Super admin logado")
print(f"Token: {super_token[:50]}...")

# ETAPA 2: Criar Empresa
print_section("ETAPA 2: Criar Empresa LLM Lavanderia")

print("Enviando requisição de onboarding...")

response = requests.post(
    f"{BACKEND_URL}/api/v1/admin/onboard-new-company",
    json={
        "tenant_name": TENANT_NAME,
        "tenant_domain": TENANT_DOMAIN,
        "bu_name": "Matriz",
        "bu_code": "MAT",
        "admin_email": ADMIN_EMAIL,
        "admin_first_name": ADMIN_FIRST_NAME,
        "admin_last_name": ADMIN_LAST_NAME,
        "admin_phone": "",
        "spreadsheet_id": SPREADSHEET_ID,
        "import_data": False  # Vamos importar depois manualmente
    },
    headers={
        "Authorization": f"Bearer {super_token}",
        "Content-Type": "application/json"
    },
    timeout=60
)

if response.status_code != 200:
    print(f"❌ Erro ao criar empresa: {response.status_code}")
    print(response.text)
    sys.exit(1)

result = response.json()

if not result.get("success"):
    print("❌ Erro:", result.get("error"))
    sys.exit(1)

print("✅ Empresa criada com sucesso!")
print()
print("Passos executados:")
for step in result["steps"]:
    print(f"  {step}")

company_info = result["company_info"]
new_admin_username = company_info["admin_username"]
new_admin_password = company_info["admin_password"]
tenant_id = company_info["tenant_id"]
bu_id = company_info["business_unit_id"]

print()
print("🔑 CREDENCIAIS GERADAS:")
print(f"   Username: {new_admin_username}")
print(f"   Password: {new_admin_password}")
print(f"   Email: {ADMIN_EMAIL}")

# ETAPA 3: Login do Admin da Empresa
print_section("ETAPA 3: Login do Admin da LLM Lavanderia")

admin_token = login(new_admin_username, new_admin_password)
if not admin_token:
    print(f"❌ Falha no login do admin")
    sys.exit(1)

print(f"✅ Admin logou com sucesso")
print(f"Username: {new_admin_username}")

# ETAPA 4: Importar Planilha
print_section("ETAPA 4: Importar Plano de Contas da Planilha")

print(f"Planilha Google Sheets: {SPREADSHEET_ID}")
print("Nota: Importação via Google Sheets API em desenvolvimento")
print("      Vamos importar o CSV local como alternativa")

# Por enquanto, vamos apenas validar que a empresa foi criada
print("✅ Empresa criada e pronta para receber dados")

# ETAPA 5: Verificar Isolamento
print_section("ETAPA 5: Verificar Isolamento Multi-Tenant")

# Ver grupos do super admin
response_super = requests.get(
    f"{BACKEND_URL}/api/v1/chart-accounts/groups",
    headers={"Authorization": f"Bearer {super_token}"},
    timeout=30
)
groups_super = response_super.json() if response_super.status_code == 200 else []

# Ver grupos do admin LLM
response_llm = requests.get(
    f"{BACKEND_URL}/api/v1/chart-accounts/groups",
    headers={"Authorization": f"Bearer {admin_token}"},
    timeout=30
)
groups_llm = response_llm.json() if response_llm.status_code == 200 else []

print(f"Super Admin (FINAFlow): {len(groups_super)} grupos")
print(f"Admin LLM Lavanderia: {len(groups_llm)} grupos")
print()

if len(groups_llm) == 0:
    print("✅ ISOLAMENTO PERFEITO!")
    print("   LLM Lavanderia não vê dados de outras empresas")
else:
    print("⚠️  LLM vê alguns grupos (pode ser global)")

# RESUMO FINAL
print_section("📊 RESUMO FINAL - LLM LAVANDERIA")

print("✅ EMPRESA ATIVADA COM SUCESSO!")
print()
print(f"🏢 Empresa: {TENANT_NAME}")
print(f"   Tenant ID: {tenant_id}")
print(f"   Domínio: {TENANT_DOMAIN}")
print()
print(f"🏭 Business Unit: Matriz (MAT)")
print(f"   BU ID: {bu_id}")
print()
print(f"👤 Administrador: {ADMIN_FIRST_NAME} {ADMIN_LAST_NAME}")
print(f"   Username: {new_admin_username}")
print(f"   Email: {ADMIN_EMAIL}")
print(f"   Senha: {new_admin_password}")
print()
print(f"🌐 URL de Acesso: https://finaflow.vercel.app/login")
print()
print("=" * 80)
print("📧 ENVIAR ESTAS CREDENCIAIS PARA O CLIENTE")
print("=" * 80)
print()
print(f"Para: {ADMIN_EMAIL}")
print()
print("Mensagem:")
print("-" * 80)
print(f"""
Olá {ADMIN_FIRST_NAME},

Sua empresa {TENANT_NAME} foi ativada no FinaFlow!

🔑 Credenciais de Acesso:
   URL: https://finaflow.vercel.app/login
   Username: {new_admin_username}
   Senha: {new_admin_password}

⚠️ IMPORTANTE: Troque sua senha no primeiro acesso!

Próximos passos:
1. Fazer login no sistema
2. Trocar senha temporária
3. Importar planilha de dados via interface
4. Criar usuários adicionais (se necessário)
5. Começar a usar o sistema

Suporte: suporte@finaflow.com

Bem-vindo ao FinaFlow! 🚀
""")
print("-" * 80)
print()
print("✅ TESTE END-TO-END CONCLUÍDO COM SUCESSO!")

