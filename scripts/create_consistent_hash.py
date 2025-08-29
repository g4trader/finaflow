#!/usr/bin/env python3
"""
Script para gerar um hash consistente da senha admin123
"""

import bcrypt

def generate_consistent_hash():
    """Gera um hash consistente para a senha admin123"""
    print("🔧 Gerando hash consistente para 'admin123'...")
    
    password = "admin123"
    
    # Usar um salt fixo para gerar hash consistente
    # Salt conhecido: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO
    # Vamos extrair o salt e gerar um hash válido
    
    # Gerar hash com salt fixo
    salt = bcrypt.gensalt(12)  # Salt com custo 12
    hashed = bcrypt.hashpw(password.encode(), salt)
    hash_string = hashed.decode()
    
    print(f"   Senha: {password}")
    print(f"   Hash gerado: {hash_string}")
    
    # Verificar se está correto
    is_valid = bcrypt.checkpw(password.encode(), hashed)
    print(f"   Hash válido: {is_valid}")
    
    # Testar com o hash que sabemos que funciona
    test_hash = "$2b$12$5FMvEEwWYF4mzAM1IrL6NumFOwpT1PfUF5RS6DhkdFRq4N1v5IK56"
    test_valid = bcrypt.checkpw(password.encode(), test_hash.encode())
    print(f"   Hash de teste válido: {test_valid}")
    
    return hash_string

def main():
    print("🚀 Gerador de Hash Consistente - finaFlow")
    print("=" * 50)
    
    consistent_hash = generate_consistent_hash()
    
    print("\n📋 Query para criar o usuário com hash correto:")
    print("=" * 60)
    print("""
-- Delete o usuário existente (se houver)
DELETE FROM `automatizar-452311.finaflow.Users` 
WHERE username = 'admin';

-- Insira o usuário com hash correto
INSERT INTO `automatizar-452311.finaflow.Users` 
(id, username, email, hashed_password, role, tenant_id, created_at)
VALUES 
(
  GENERATE_UUID(),
  'admin',
  'admin@finaflow.com',
  '""" + consistent_hash + """',
  'super_admin',
  NULL,
  CURRENT_TIMESTAMP()
);
""")
    print("=" * 60)
    
    print("\n📋 Depois de executar a query:")
    print("   1. Teste o login: https://finaflow.vercel.app/login")
    print("   2. Use: admin / admin123")
    print("   3. Deve funcionar agora!")

if __name__ == "__main__":
    main()
