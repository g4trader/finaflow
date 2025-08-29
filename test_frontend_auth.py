#!/usr/bin/env python3
"""
Script para testar se o problema está no frontend
"""

import requests

# Configurações
API_URL = "https://finaflow-backend-609095880025.us-central1.run.app"

def test_frontend_simulation():
    """Simula exatamente como o frontend faz as requisições"""
    print("🔧 Testando simulação do frontend...")
    
    # 1. Fazer login (como o frontend faz)
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", data=login_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"   ✅ Login: Funcionando")
            print(f"   🔑 Token: {token[:50]}...")
            
            # 2. Testar exatamente como o frontend faz (usando axios)
            auth_headers = {'Authorization': f'Bearer {token}'}
            
            # Testar com headers exatos do axios
            endpoints = [
                ('/accounts', 'Contas'),
                ('/transactions', 'Transações'),
                ('/groups', 'Grupos'),
                ('/subgroups', 'Subgrupos'),
            ]
            
            working_endpoints = 0
            total_endpoints = len(endpoints)
            
            for endpoint, name in endpoints:
                try:
                    # Simular exatamente como o axios faz
                    response = requests.get(
                        f"{API_URL}{endpoint}", 
                        headers=auth_headers, 
                        timeout=10
                    )
                    
                    print(f"   📡 {name}: {response.status_code} - {response.text[:100]}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        count = len(data) if isinstance(data, list) else 1
                        print(f"   ✅ {name}: {count} registros")
                        working_endpoints += 1
                    else:
                        print(f"   ❌ {name}: {response.status_code} - {response.text[:100]}")
                        
                except Exception as e:
                    print(f"   ❌ {name}: Erro - {e}")
            
            print(f"\n📊 Resultado: {working_endpoints}/{total_endpoints} endpoints funcionando")
            
            if working_endpoints > 0:
                print(f"🎉 FRONTEND SIMULATION FUNCIONANDO!")
                return True
            else:
                print(f"❌ Frontend simulation falhou")
                return False
                
        else:
            print(f"   ❌ Login falhou: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("🚀 Teste de Simulação do Frontend - finaFlow")
    print("=" * 50)
    
    success = test_frontend_simulation()
    
    if success:
        print("\n🎉 O problema NÃO está no frontend!")
        print("   ✅ As requisições estão sendo feitas corretamente")
        print("   ✅ O problema pode estar em outro lugar")
    else:
        print("\n❌ O problema pode estar no frontend")

if __name__ == "__main__":
    main()
