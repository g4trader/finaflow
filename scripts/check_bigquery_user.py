#!/usr/bin/env python3
"""
Script para verificar diretamente o usuário no BigQuery
"""

import requests
import json

# Configurações
BACKEND_URL = "https://finaflow-backend-609095880025.us-central1.run.app"

def test_bigquery_query():
    """Testa a consulta que o backend faz no BigQuery"""
    print("🔍 Testando consulta do BigQuery...")
    
    # Simular a consulta que o backend faz
    # O backend usa: query("Users", {"username": username})
    
    print("   O backend executa esta consulta:")
    print("   SELECT * FROM `trivihair.finaflow.Users` WHERE username='admin'")
    
    # Vamos testar se conseguimos acessar a documentação da API
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend está funcionando")
        else:
            print(f"   ❌ Backend não está funcionando: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Erro ao conectar ao backend: {e}")
        return
    
    print("\n📋 Verifique no BigQuery:")
    print("   1. Execute esta query:")
    print("      SELECT * FROM `trivihair.finaflow.Users` WHERE username='admin'")
    print("\n   2. Verifique se retorna exatamente:")
    print("      - username: 'admin' (exatamente assim)")
    print("      - hashed_password: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO'")
    print("      - role: 'super_admin'")
    print("      - email: 'admin@finaflow.com'")
    
    print("\n🔧 Possíveis problemas:")
    print("   1. Username com espaços extras")
    print("   2. Hash da senha diferente")
    print("   3. Case sensitivity (admin vs Admin)")
    print("   4. Caracteres especiais no username")

def create_correct_user_query():
    """Gera a query correta para criar o usuário"""
    print("\n🔧 Query para recriar o usuário corretamente:")
    print("=" * 60)
    print("""
-- Primeiro, delete o usuário existente (se houver)
DELETE FROM `trivihair.finaflow.Users` 
WHERE username = 'admin';

-- Depois, insira o usuário correto
INSERT INTO `trivihair.finaflow.Users` 
(id, username, email, hashed_password, role, tenant_id, created_at)
VALUES 
(
  GENERATE_UUID(),
  'admin',
  'admin@finaflow.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO',
  'super_admin',
  NULL,
  CURRENT_TIMESTAMP()
);
""")
    print("=" * 60)

def main():
    print("🚀 Verificação do BigQuery - finaFlow")
    print("=" * 50)
    
    test_bigquery_query()
    create_correct_user_query()
    
    print("\n📋 Próximos passos:")
    print("   1. Execute as queries no BigQuery")
    print("   2. Teste o login novamente")
    print("   3. Se ainda não funcionar, me informe o resultado da query SELECT")

if __name__ == "__main__":
    main()
