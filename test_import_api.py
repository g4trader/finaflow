"""
Teste da API de importação de dados do Google Sheets
"""

import requests
import json
import os
from datetime import datetime

# Configuração
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
TEST_USERNAME = os.getenv("TEST_USERNAME", "admin")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "admin123")
SPREADSHEET_ID = "1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY"

def test_import_api():
    """Testar a API de importação"""
    
    print("🚀 Testando API de Importação - Google Sheets")
    print("=" * 60)
    
    # 1. Fazer login para obter token
    print("🔐 Fazendo login...")
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data=login_data,
            timeout=10
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login realizado com sucesso!")
        else:
            print(f"❌ Erro no login: {login_response.status_code}")
            print(f"Resposta: {login_response.text}")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return
    
    # 2. Testar endpoint de informações da planilha de exemplo
    print("\n📋 Testando informações da planilha de exemplo...")
    try:
        sample_response = requests.get(
            f"{BACKEND_URL}/api/v1/import/google-sheets/sample",
            headers=headers,
            timeout=10
        )
        
        if sample_response.status_code == 200:
            sample_data = sample_response.json()
            print("✅ Informações da planilha obtidas:")
            print(f"   - ID: {sample_data['spreadsheet_id']}")
            print(f"   - Descrição: {sample_data['description']}")
            print(f"   - Total de abas: {len(sample_data['sheets'])}")
            print(f"   - Primeiras 5 abas: {sample_data['sheets'][:5]}")
        else:
            print(f"❌ Erro ao obter informações: {sample_response.status_code}")
            print(f"Resposta: {sample_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 3. Testar validação da planilha
    print(f"\n🔍 Testando validação da planilha {SPREADSHEET_ID}...")
    try:
        validate_response = requests.post(
            f"{BACKEND_URL}/api/v1/import/google-sheets/validate",
            params={"spreadsheet_id": SPREADSHEET_ID},
            headers=headers,
            timeout=30
        )
        
        if validate_response.status_code == 200:
            validate_data = validate_response.json()
            print("✅ Validação concluída:")
            print(f"   - Sucesso: {validate_data['success']}")
            print(f"   - Título: {validate_data.get('spreadsheet_title', 'N/A')}")
            print(f"   - Abas encontradas: {len(validate_data['sheets_found'])}")
            print(f"   - Estrutura de dados: {validate_data['data_structure']['total_sheets']} abas totais")
            
            if validate_data.get('validation_errors'):
                print(f"   - Erros de validação: {len(validate_data['validation_errors'])}")
                for error in validate_data['validation_errors'][:3]:  # Mostrar apenas os primeiros 3
                    print(f"     • {error}")
            else:
                print("   - ✅ Nenhum erro de validação encontrado")
                
        else:
            print(f"❌ Erro na validação: {validate_response.status_code}")
            print(f"Resposta: {validate_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 4. Testar importação (apenas validação)
    print(f"\n📥 Testando importação (modo validação) da planilha {SPREADSHEET_ID}...")
    try:
        import_request = {
            "spreadsheet_id": SPREADSHEET_ID,
            "import_type": "all",
            "validate_only": True
        }
        
        import_response = requests.post(
            f"{BACKEND_URL}/api/v1/import/google-sheets",
            json=import_request,
            headers=headers,
            timeout=30
        )
        
        if import_response.status_code == 200:
            import_data = import_response.json()
            print("✅ Importação (validação) concluída:")
            print(f"   - Sucesso: {import_data['success']}")
            print(f"   - Mensagem: {import_data['message']}")
            print(f"   - Título: {import_data.get('spreadsheet_title', 'N/A')}")
            
            if import_data.get('errors'):
                print(f"   - Erros: {len(import_data['errors'])}")
                for error in import_data['errors'][:3]:  # Mostrar apenas os primeiros 3
                    print(f"     • {error}")
            else:
                print("   - ✅ Nenhum erro encontrado")
                
        else:
            print(f"❌ Erro na importação: {import_response.status_code}")
            print(f"Resposta: {import_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 5. Testar importação real (comentada para não executar)
    print(f"\n💡 Para testar importação real, descomente o código abaixo:")
    print(f"""
    # import_request = {{
    #     "spreadsheet_id": "{SPREADSHEET_ID}",
    #     "import_type": "all",
    #     "validate_only": False
    # }}
    # 
    # import_response = requests.post(
    #     f"{BACKEND_URL}/api/v1/import/google-sheets",
    #     json=import_request,
    #     headers=headers,
    #     timeout=60
    # )
    # 
    # if import_response.status_code == 200:
    #     import_data = import_response.json()
    #     print("✅ Importação real concluída:")
    #     print(f"   - Sucesso: {{import_data['success']}}")
    #     print(f"   - Dados importados: {{import_data.get('data_imported', {{}})}}")
    # else:
    #     print(f"❌ Erro na importação: {{import_response.status_code}}")
    """)
    
    print("\n" + "=" * 60)
    print("🎉 Teste da API de Importação concluído!")
    print("📋 Verifique os resultados acima para identificar possíveis problemas.")

if __name__ == "__main__":
    test_import_api()







