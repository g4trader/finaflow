#!/usr/bin/env python3
"""
Script para monitorar o onboarding da empresa LLM e avisar quando concluir
"""

import os
import sys
import requests
import time
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://finaflow-backend-staging-642830139828.us-central1.run.app"
)
QA_USERNAME = os.getenv("QA_USERNAME", "qa@finaflow.test")
QA_PASSWORD = os.getenv("QA_PASSWORD", "QaFinaflow123!")

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

def find_llm_tenant_and_bu(headers):
    """Encontra tenant e BU LLM"""
    # Tentar diferentes endpoints
    endpoints = [
        "/api/v1/tenants",
        "/api/v1/auth/tenants",
    ]
    
    tenants = None
    for endpoint in endpoints:
        resp = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=30)
        if resp.status_code == 200:
            tenants = resp.json()
            break
    
    if not tenants:
        # Tentar buscar via user-business-units
        bu_resp = requests.get(f"{BACKEND_URL}/api/v1/auth/user-business-units", headers=headers, timeout=30)
        if bu_resp.status_code == 200:
            bus = bu_resp.json()
            # Assumir que a primeira BU é da LLM (ou buscar por nome)
            for bu in bus:
                if isinstance(bu, dict):
                    bu_id = bu.get("id", "")
                    tenant_id = bu.get("tenant_id", "")
                else:
                    bu_id = getattr(bu, "id", "")
                    tenant_id = getattr(bu, "tenant_id", "")
                
                if tenant_id and bu_id:
                    # Verificar se é LLM pelo tenant_id (assumir que é o mais recente criado)
                    return tenant_id, bu_id
        return None, None
    
    llm_tenant = None
    
    for tenant in tenants:
        if isinstance(tenant, dict):
            name = tenant.get("name", "")
            tenant_id = tenant.get("id", "")
        else:
            name = getattr(tenant, "name", "")
            tenant_id = getattr(tenant, "id", "")
        
        if "llm" in name.lower():
            llm_tenant = {"id": tenant_id, "name": name}
            break
    
    if not llm_tenant:
        return None, None
    
    # Buscar Business Units
    resp = requests.get(
        f"{BACKEND_URL}/api/v1/business-units",
        headers=headers,
        params={"tenant_id": llm_tenant["id"]},
        timeout=30
    )
    
    if resp.status_code == 200:
        bus = resp.json()
        if isinstance(bus, list) and len(bus) > 0:
            bu = bus[0]
            bu_id = bu.get("id") if isinstance(bu, dict) else getattr(bu, "id", "")
            if bu_id:
                return llm_tenant["id"], bu_id
    
    return llm_tenant["id"], None

def monitor_onboarding(headers, tenant_id, business_unit_id, check_interval=10, max_wait=1800):
    """Monitora onboarding e avisa quando concluir"""
    print("="*60)
    print("🔍 MONITORANDO ONBOARDING LLM")
    print("="*60)
    print(f"Tenant ID: {tenant_id}")
    print(f"Business Unit ID: {business_unit_id or 'Será criada pelo seed'}")
    print(f"Intervalo de verificação: {check_interval} segundos")
    print(f"Timeout máximo: {max_wait} segundos ({max_wait//60} minutos)")
    print("="*60)
    print("\n⏳ Aguardando conclusão do onboarding...\n")
    
    start_time = time.time()
    last_progress = -1
    last_status = None
    
    while time.time() - start_time < max_wait:
        try:
            # Se não tiver BU ainda, tentar buscar novamente
            if not business_unit_id:
                _, business_unit_id = find_llm_tenant_and_bu(headers)
                if not business_unit_id:
                    print("⏳ Aguardando criação da Business Unit...")
                    time.sleep(check_interval)
                    continue
            
            resp = requests.get(
                f"{BACKEND_URL}/api/v1/onboarding/status/{tenant_id}/{business_unit_id}",
                headers=headers,
                timeout=30
            )
            
            if resp.status_code == 200:
                status = resp.json()
                current_status = status.get("status", "")
                current_progress = status.get("progress", 0)
                current_step = status.get("current_step", "")
                message = status.get("message", "")
                
                # Só imprimir se mudou
                if current_status != last_status or current_progress != last_progress:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] {current_progress}% - {current_step}")
                    if message and message != "Onboarding não iniciado":
                        print(f"         {message}")
                    last_status = current_status
                    last_progress = current_progress
                
                # Verificar se concluiu
                if current_status == "completed":
                    elapsed = int(time.time() - start_time)
                    print("\n" + "="*60)
                    print("✅✅✅ ONBOARDING CONCLUÍDO COM SUCESSO!")
                    print("="*60)
                    print(f"⏱️  Tempo total: {elapsed//60} minutos e {elapsed%60} segundos")
                    
                    if status.get("stats"):
                        print("\n📊 Estatísticas finais:")
                        for key, value in status["stats"].items():
                            print(f"   {key}: {value}")
                    
                    print(f"\n🔗 Verifique a conciliação em:")
                    print(f"   /admin/reconciliation?tenant_id={tenant_id}&business_unit_id={business_unit_id}")
                    print("="*60)
                    
                    # Aviso visual e sonoro (se possível)
                    print("\n🔔🔔🔔 PROCESSO CONCLUÍDO! 🔔🔔🔔")
                    print("\n" + "="*60)
                    return True
                
                elif current_status == "error":
                    print("\n" + "="*60)
                    print("❌ ERRO DURANTE ONBOARDING")
                    print("="*60)
                    print(f"Mensagem: {message}")
                    if status.get("errors"):
                        print("\nErros encontrados:")
                        for err in status["errors"]:
                            print(f"   - {err}")
                    print("="*60)
                    return False
            
            elif resp.status_code == 404:
                # Onboarding ainda não iniciado
                if last_status != "not_started":
                    print("⏳ Aguardando início do onboarding...")
                    last_status = "not_started"
            
        except Exception as e:
            print(f"⚠️  Erro ao verificar status: {e}")
        
        time.sleep(check_interval)
    
    print("\n" + "="*60)
    print("⏱️  TIMEOUT: Onboarding demorou mais que o esperado")
    print("="*60)
    print("Verifique manualmente o status via API ou interface")
    return False

def main():
    """Função principal"""
    try:
        # Login
        print("🔐 Fazendo login...")
        token = login()
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login realizado\n")
        
        # Encontrar tenant e BU LLM
        print("🔍 Buscando empresa LLM...")
        tenant_id, business_unit_id = find_llm_tenant_and_bu(headers)
        
        if not tenant_id:
            print("❌ Empresa LLM não encontrada")
            print("   Execute primeiro o script clean_and_onboard_llm.py")
            return 1
        
        print(f"✅ Empresa LLM encontrada (Tenant ID: {tenant_id})")
        if business_unit_id:
            print(f"✅ Business Unit encontrada (ID: {business_unit_id})")
        else:
            print("⚠️  Business Unit será criada pelo seed")
        
        # Monitorar
        success = monitor_onboarding(headers, tenant_id, business_unit_id)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoramento interrompido pelo usuário")
        return 1
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

