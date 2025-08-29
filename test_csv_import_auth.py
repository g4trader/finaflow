#!/usr/bin/env python3
"""
Script para testar se a rota CSV import está funcionando com autenticação
"""

import requests

# Configurações
API_URL = "https://finaflow-backend-609095880025.us-central1.run.app"

def test_csv_import_auth():
    """Testa se a rota CSV import está funcionando com autenticação"""
    print("🔧 Testando rota CSV import com autenticação...")
    
    # 1. Fazer login
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
            print(f"   🔑 Token: Gerado com sucesso")
            
            # 2. Testar rota CSV import
            auth_headers = {'Authorization': f'Bearer {token}'}
            
            # Testar template endpoint (não requer arquivo)
            try:
                response = requests.get(f"{API_URL}/csv/template/plan-accounts", headers=auth_headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ CSV Template: Funcionando")
                    print(f"   📄 Template: {data.get('filename')}")
                    return True
                else:
                    print(f"   ❌ CSV Template: {response.status_code} - {response.text[:100]}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ CSV Template: Erro - {e}")
                return False
                
        else:
            print(f"   ❌ Login falhou: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("🚀 Teste da Rota CSV Import - finaFlow")
    print("=" * 50)
    
    success = test_csv_import_auth()
    
    if success:
        print("\n🎉 ROTA CSV IMPORT FUNCIONANDO!")
        print("   ✅ Autenticação está funcionando para esta rota")
        print("   ✅ Podemos usar como base para corrigir outras rotas")
    else:
        print("\n❌ Rota CSV import também não está funcionando")

if __name__ == "__main__":
    main()
