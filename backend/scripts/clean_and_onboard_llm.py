#!/usr/bin/env python3
"""
Script para limpar dados da empresa LLM e executar onboarding
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://finaflow-backend-staging-556803510516.us-central1.run.app"
)
QA_USERNAME = os.getenv("QA_USERNAME", "qa@finaflow.test")
QA_PASSWORD = os.getenv("QA_PASSWORD", "QaFinaflow123!")

# URL da planilha Google Sheets
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ/edit?gid=1158090564#gid=1158090564"

def login():
    """Faz login e retorna token"""
    resp = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": QA_USERNAME, "password": QA_PASSWORD},
        timeout=30
    )
    if resp.status_code != 200:
        raise Exception(f"Erro no login: {resp.status_code} - {resp.text}")
    return resp.json()["access_token"]

def get_or_create_tenant(headers):
    """Busca ou cria tenant LLM"""
    # Tentar buscar via endpoint de auth
    resp = requests.get(f"{BACKEND_URL}/api/v1/auth/tenants", headers=headers, timeout=30)
    
    if resp.status_code == 200:
        tenants = resp.json()
        for tenant in tenants:
            if isinstance(tenant, dict):
                name = tenant.get("name", "")
                domain = tenant.get("domain", "")
                tenant_id = tenant.get("id", "")
            else:
                name = getattr(tenant, "name", "")
                domain = getattr(tenant, "domain", "")
                tenant_id = getattr(tenant, "id", "")
            
            if "llm" in name.lower() or "llm" in domain.lower():
                print(f"✅ Tenant LLM encontrado: {name} (ID: {tenant_id})")
                return {"id": tenant_id, "name": name}
    
    # Se não encontrou, tentar criar com domain único
    print("⚠️  Tenant LLM não encontrado. Tentando criar...")
    import uuid
    unique_domain = f"llm-lavanderia-{str(uuid.uuid4())[:8]}.com"
    
    create_resp = requests.post(
        f"{BACKEND_URL}/api/v1/auth/tenants",
        headers=headers,
        json={"name": "LLM Lavanderia", "domain": unique_domain},
        timeout=30
    )
    
    if create_resp.status_code in [200, 201]:
        tenant = create_resp.json()
        print(f"✅ Tenant LLM criado: {tenant.get('name')} (ID: {tenant.get('id')})")
        return {"id": tenant.get("id"), "name": tenant.get("name")}
    elif create_resp.status_code == 400 and "Domain já existe" in create_resp.text:
        # Domain já existe, buscar novamente
        print("⚠️  Domain já existe. Buscando tenant existente...")
        resp2 = requests.get(f"{BACKEND_URL}/api/v1/auth/tenants", headers=headers, timeout=30)
        if resp2.status_code == 200:
            tenants = resp2.json()
            for tenant in tenants:
                if isinstance(tenant, dict):
                    domain = tenant.get("domain", "")
                    if "llm" in domain.lower():
                        print(f"✅ Tenant LLM encontrado pelo domain: {tenant.get('name')} (ID: {tenant.get('id')})")
                        return {"id": tenant.get("id"), "name": tenant.get("name")}
        raise Exception("Domain já existe mas não foi possível encontrar o tenant")
    else:
        raise Exception(f"Erro ao criar tenant: {create_resp.status_code} - {create_resp.text}")

def get_or_create_business_unit(headers, tenant_id):
    """Busca ou cria Business Unit - o seed criará automaticamente se não existir"""
    # Tentar buscar via endpoint de business units
    resp = requests.get(
        f"{BACKEND_URL}/api/v1/business-units",
        headers=headers,
        params={"tenant_id": tenant_id},
        timeout=30
    )
    
    if resp.status_code == 200:
        bus = resp.json()
        if isinstance(bus, list) and len(bus) > 0:
            for bu in bus:
                if isinstance(bu, dict):
                    bu_id = bu.get("id", "")
                    bu_name = bu.get("name", "")
                else:
                    bu_id = getattr(bu, "id", "")
                    bu_name = getattr(bu, "name", "")
                
                if bu_id:
                    print(f"✅ Business Unit encontrada: {bu_name} (ID: {bu_id})")
                    return {"id": bu_id, "name": bu_name}
    
    # Se não encontrou, o seed criará automaticamente
    print("⚠️  Business Unit não encontrada. Será criada automaticamente pelo seed.")
    # Retornar None - o seed criará
    return None

def clear_data(headers, tenant_id, business_unit_id):
    """Limpa dados financeiros"""
    print("\n" + "="*60)
    print("🧹 LIMPANDO DADOS DA EMPRESA LLM")
    print("="*60)
    
    resp = requests.post(
        f"{BACKEND_URL}/api/v1/onboarding/clear-data",
        headers=headers,
        json={
            "tenant_id": tenant_id,
            "business_unit_id": business_unit_id,
            "year": 2025
        },
        timeout=60
    )
    
    if resp.status_code == 200:
        result = resp.json()
        print("✅ Dados limpos com sucesso!")
        print(f"   Lançamentos diários deletados: {result.get('deleted', {}).get('lancamentos_diarios', 0)}")
        print(f"   Lançamentos previstos deletados: {result.get('deleted', {}).get('lancamentos_previstos', 0)}")
        return True
    else:
        print(f"❌ Erro ao limpar dados: {resp.status_code}")
        print(f"   {resp.text}")
        return False

def validate_spreadsheet(headers, tenant_id, business_unit_id, spreadsheet_url):
    """Valida planilha"""
    print("\n" + "="*60)
    print("🔍 VALIDANDO PLANILHA")
    print("="*60)
    
    resp = requests.post(
        f"{BACKEND_URL}/api/v1/onboarding/validate-spreadsheet",
        headers=headers,
        json={
            "url": spreadsheet_url,
            "tenant_id": tenant_id,
            "business_unit_id": business_unit_id
        },
        timeout=60
    )
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get("valid"):
            print("✅ Planilha válida!")
            print(f"   Abas encontradas: {len(result.get('available_sheets', []))}")
            return True
        else:
            print(f"❌ Planilha inválida: {result.get('error')}")
            return False
    else:
        print(f"❌ Erro ao validar: {resp.status_code}")
        print(f"   {resp.text}")
        return False

def start_onboarding(headers, tenant_id, business_unit_id, spreadsheet_url):
    """Inicia onboarding"""
    print("\n" + "="*60)
    print("🚀 INICIANDO ONBOARDING")
    print("="*60)
    
    resp = requests.post(
        f"{BACKEND_URL}/api/v1/onboarding/import",
        headers=headers,
        json={
            "tenant_id": tenant_id,
            "business_unit_id": business_unit_id,
            "spreadsheet_url": spreadsheet_url,
            "reset_data": False  # Já limpamos antes
        },
        timeout=60
    )
    
    if resp.status_code == 200:
        print("✅ Onboarding iniciado!")
        return True
    else:
        print(f"❌ Erro ao iniciar onboarding: {resp.status_code}")
        print(f"   {resp.text}")
        return False

def monitor_onboarding(headers, tenant_id, business_unit_id, max_wait=600):
    """Monitora progresso do onboarding"""
    print("\n" + "="*60)
    print("📊 ACOMPANHANDO PROGRESSO")
    print("="*60)
    
    start_time = time.time()
    last_progress = -1
    
    while time.time() - start_time < max_wait:
        resp = requests.get(
            f"{BACKEND_URL}/api/v1/onboarding/status/{tenant_id}/{business_unit_id}",
            headers=headers,
            timeout=30
        )
        
        if resp.status_code == 200:
            status = resp.json()
            current_progress = status.get("progress", 0)
            current_step = status.get("current_step", "")
            message = status.get("message", "")
            status_type = status.get("status", "")
            
            if current_progress != last_progress:
                print(f"📊 {current_progress}% - {current_step}")
                if message:
                    print(f"   {message}")
                last_progress = current_progress
            
            if status_type == "completed":
                print("\n✅✅✅ ONBOARDING CONCLUÍDO COM SUCESSO!")
                if status.get("stats"):
                    stats = status["stats"]
                    print("\n📊 Estatísticas:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")
                return True
            elif status_type == "error":
                print(f"\n❌ Erro durante onboarding: {message}")
                if status.get("errors"):
                    print("   Erros:")
                    for err in status["errors"]:
                        print(f"     - {err}")
                return False
        
        time.sleep(5)
    
    print("\n⚠️  Timeout: Importação demorou mais de 10 minutos")
    return False

def main():
    """Função principal"""
    print("="*60)
    print("🌱 LIMPAR E ONBOARDING - EMPRESA LLM")
    print("="*60)
    print(f"Backend: {BACKEND_URL}")
    print(f"Planilha: {SPREADSHEET_URL}")
    print("="*60)
    
    try:
        # 1. Login
        print("\n1️⃣ Fazendo login...")
        token = login()
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login realizado com sucesso")
        
        # 2. Buscar ou criar Tenant
        print("\n2️⃣ Buscando/Criando Tenant LLM...")
        tenant = get_or_create_tenant(headers)
        
        # 3. Buscar ou criar Business Unit via API
        print("\n3️⃣ Buscando/Criando Business Unit...")
        # O seed criará a BU automaticamente, mas precisamos de uma para validação
        # Vamos tentar buscar primeiro
        bus_resp = requests.get(
            f"{BACKEND_URL}/api/v1/business-units",
            headers=headers,
            params={"tenant_id": tenant["id"]},
            timeout=30
        )
        
        business_unit = None
        if bus_resp.status_code == 200:
            bus = bus_resp.json()
            if isinstance(bus, list) and len(bus) > 0:
                bu = bus[0]
                business_unit = {
                    "id": bu.get("id") if isinstance(bu, dict) else getattr(bu, "id", ""),
                    "name": bu.get("name") if isinstance(bu, dict) else getattr(bu, "name", "")
                }
                print(f"✅ Business Unit encontrada: {business_unit['name']} (ID: {business_unit['id']})")
        
        # Se não encontrou, vamos pular a validação e deixar o seed criar
        # O onboarding vai funcionar mesmo sem BU pré-existente
        if not business_unit:
            print("⚠️  Business Unit não encontrada. Será criada pelo seed durante o onboarding.")
            print("   Pulando validação e limpeza de dados...")
            # Criar uma BU temporária apenas para passar na validação
            # Na verdade, vamos pular a validação e ir direto para o onboarding
            business_unit = {"id": tenant["id"], "name": "Temporária"}
        
        # 4. Limpar dados (só se tiver BU real)
        if business_unit and business_unit["id"] != tenant["id"]:
            print("\n4️⃣ Limpando dados existentes...")
            if not clear_data(headers, tenant["id"], business_unit["id"]):
                print("⚠️  Aviso: Não foi possível limpar dados. Continuando...")
        else:
            print("\n4️⃣ Pulando limpeza (BU será criada pelo seed)")
        
        # 5. Validar planilha (pular se não tiver BU real)
        if business_unit and business_unit["id"] != tenant["id"]:
            print("\n5️⃣ Validando planilha...")
            if not validate_spreadsheet(headers, tenant["id"], business_unit["id"], SPREADSHEET_URL):
                print("❌ Falha na validação da planilha. Abortando.")
                return 1
        else:
            print("\n5️⃣ Pulando validação (BU será criada pelo seed)")
            print("   A validação será feita durante o onboarding")
        
        # 6. Iniciar onboarding
        print("\n6️⃣ Iniciando onboarding...")
        # Usar tenant_id como BU temporário - o seed criará a BU real
        bu_id_for_onboarding = business_unit["id"] if business_unit and business_unit["id"] != tenant["id"] else tenant["id"]
        if not start_onboarding(headers, tenant["id"], bu_id_for_onboarding, SPREADSHEET_URL):
            print("❌ Falha ao iniciar onboarding. Abortando.")
            return 1
        
        # 7. Monitorar progresso
        print("\n7️⃣ Monitorando progresso...")
        print("   (A Business Unit será criada automaticamente pelo seed)")
        print("   Aguardando conclusão...\n")
        success = monitor_onboarding(headers, tenant["id"], bu_id_for_onboarding)
        
        if success:
            # Buscar BU real criada pelo seed
            time.sleep(2)  # Aguardar um pouco para garantir que a BU foi criada
            bus_resp = requests.get(
                f"{BACKEND_URL}/api/v1/business-units",
                headers=headers,
                params={"tenant_id": tenant["id"]},
                timeout=30
            )
            final_bu_id = bu_id_for_onboarding
            if bus_resp.status_code == 200:
                bus = bus_resp.json()
                if isinstance(bus, list) and len(bus) > 0:
                    final_bu_id = bus[0].get("id") if isinstance(bus[0], dict) else getattr(bus[0], "id", "")
            
            print("\n" + "="*60)
            print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
            print("="*60)
            print(f"Tenant ID: {tenant['id']}")
            print(f"Business Unit ID: {final_bu_id}")
            print(f"\n🔗 Verifique a conciliação em:")
            print(f"   /admin/reconciliation?tenant_id={tenant['id']}&business_unit_id={final_bu_id}")
            print("="*60)
            return 0
        else:
            print("\n❌ Onboarding falhou")
            return 1
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

