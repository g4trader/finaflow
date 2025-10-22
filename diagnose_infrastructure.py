#!/usr/bin/env python3
"""
Script para diagnosticar a infraestrutura atual do FinaFlow
Verifica: backend, banco de dados, dados migrados, configurações
"""
import requests
import json
from datetime import datetime

BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def diagnose():
    report = {
        "timestamp": datetime.now().isoformat(),
        "backend_url": BACKEND_URL,
        "checks": {}
    }
    
    print_section("🔍 DIAGNÓSTICO DA INFRAESTRUTURA FINAFLOW")
    
    # 1. Verificar Backend está online
    print("\n1️⃣ Verificando Backend...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        report["checks"]["backend_online"] = response.status_code == 200
        print(f"   ✅ Backend online: {response.status_code}")
    except Exception as e:
        report["checks"]["backend_online"] = False
        print(f"   ❌ Backend offline: {e}")
        return report
    
    # 2. Testar Login
    print("\n2️⃣ Testando Login...")
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            report["checks"]["login"] = True
            print(f"   ✅ Login OK - Token obtido")
        else:
            report["checks"]["login"] = False
            print(f"   ❌ Login falhou: {login_response.status_code}")
            return report
            
    except Exception as e:
        report["checks"]["login"] = False
        print(f"   ❌ Erro no login: {e}")
        return report
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Verificar Business Units
    print("\n3️⃣ Verificando Business Units...")
    try:
        bu_response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/user-business-units",
            headers=headers,
            timeout=10
        )
        
        if bu_response.status_code == 200:
            business_units = bu_response.json()
            report["checks"]["business_units"] = {
                "status": "success",
                "count": len(business_units),
                "data": business_units
            }
            print(f"   ✅ Business Units: {len(business_units)} encontrada(s)")
            for bu in business_units:
                print(f"      - {bu['tenant_name']} > {bu['name']} (ID: {bu['id']})")
        else:
            report["checks"]["business_units"] = {"status": "error", "code": bu_response.status_code}
            print(f"   ❌ Erro ao buscar BUs: {bu_response.status_code}")
            
    except Exception as e:
        report["checks"]["business_units"] = {"status": "error", "message": str(e)}
        print(f"   ❌ Erro: {e}")
    
    # 4. Testar Seleção de Business Unit
    if report["checks"]["business_units"].get("count", 0) > 0:
        print("\n4️⃣ Testando Seleção de Business Unit...")
        business_unit_id = business_units[0]['id']
        
        try:
            select_response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/select-business-unit",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"business_unit_id": business_unit_id},
                timeout=10
            )
            
            if select_response.status_code == 200:
                select_data = select_response.json()
                report["checks"]["select_bu"] = {"status": "success", "data": select_data}
                print(f"   ✅ Seleção OK")
                print(f"      - Empresa: {select_data['user']['tenant_name']}")
                print(f"      - Unidade: {select_data['user']['business_unit_name']}")
            else:
                report["checks"]["select_bu"] = {
                    "status": "error",
                    "code": select_response.status_code,
                    "message": select_response.text
                }
                print(f"   ❌ Seleção falhou: {select_response.status_code}")
                print(f"      Resposta: {select_response.text}")
                
        except Exception as e:
            report["checks"]["select_bu"] = {"status": "error", "message": str(e)}
            print(f"   ❌ Erro: {e}")
    
    # 5. Verificar OpenAPI/Documentação
    print("\n5️⃣ Verificando Endpoints Disponíveis...")
    try:
        openapi_response = requests.get(f"{BACKEND_URL}/openapi.json", timeout=10)
        if openapi_response.status_code == 200:
            openapi = openapi_response.json()
            endpoints = list(openapi.get("paths", {}).keys())
            report["checks"]["endpoints"] = {
                "status": "success",
                "count": len(endpoints),
                "list": endpoints[:10]  # Primeiros 10
            }
            print(f"   ✅ {len(endpoints)} endpoints disponíveis")
            print(f"      Alguns exemplos:")
            for ep in endpoints[:5]:
                print(f"      - {ep}")
        else:
            report["checks"]["endpoints"] = {"status": "error"}
            print(f"   ❌ Erro ao obter OpenAPI")
    except Exception as e:
        report["checks"]["endpoints"] = {"status": "error", "message": str(e)}
        print(f"   ❌ Erro: {e}")
    
    # 6. Resumo
    print_section("📊 RESUMO DO DIAGNÓSTICO")
    
    success_count = sum(1 for check in report["checks"].values() 
                       if isinstance(check, bool) and check or 
                       isinstance(check, dict) and check.get("status") == "success")
    total_count = len(report["checks"])
    
    print(f"\n✅ Checks bem-sucedidos: {success_count}/{total_count}")
    print(f"\n🔍 Detalhes:")
    print(f"   - Backend online: {'✅' if report['checks'].get('backend_online') else '❌'}")
    print(f"   - Login funciona: {'✅' if report['checks'].get('login') else '❌'}")
    print(f"   - Business Units: {'✅' if report['checks'].get('business_units', {}).get('status') == 'success' else '❌'}")
    print(f"   - Seleção de BU: {'✅' if report['checks'].get('select_bu', {}).get('status') == 'success' else '❌'}")
    print(f"   - Endpoints: {'✅' if report['checks'].get('endpoints', {}).get('status') == 'success' else '❌'}")
    
    # Salvar relatório
    report_file = f"/tmp/finaflow_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, indent=2, fp=f)
    
    print(f"\n💾 Relatório salvo em: {report_file}")
    
    return report

if __name__ == "__main__":
    diagnose()


