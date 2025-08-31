#!/usr/bin/env python3
"""
Script para testar a inicialização do banco de dados
"""

import os
import sys

# Configurar variáveis de ambiente
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.42.61.193:5432/finaflow_db"

try:
    print("🔧 Testando importação dos módulos...")
    
    # Importar módulos básicos
    from app.database import engine, Base, create_tables
    print("✅ Módulos básicos importados com sucesso")
    
    # Importar modelos de autenticação
    from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess
    print("✅ Modelos de autenticação importados com sucesso")
    
    # Importar modelos do plano de contas
    from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account
    print("✅ Modelos do plano de contas importados com sucesso")
    
    # Testar criação das tabelas
    print("🔧 Testando criação das tabelas...")
    create_tables()
    print("✅ Tabelas criadas com sucesso")
    
    print("🎉 Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
Script para testar a inicialização do banco de dados
"""

import os
import sys

# Configurar variáveis de ambiente
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.42.61.193:5432/finaflow_db"

try:
    print("🔧 Testando importação dos módulos...")
    
    # Importar módulos básicos
    from app.database import engine, Base, create_tables
    print("✅ Módulos básicos importados com sucesso")
    
    # Importar modelos de autenticação
    from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess
    print("✅ Modelos de autenticação importados com sucesso")
    
    # Importar modelos do plano de contas
    from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account
    print("✅ Modelos do plano de contas importados com sucesso")
    
    # Testar criação das tabelas
    print("🔧 Testando criação das tabelas...")
    create_tables()
    print("✅ Tabelas criadas com sucesso")
    
    print("🎉 Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
Script para testar a inicialização do banco de dados
"""

import os
import sys

# Configurar variáveis de ambiente
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.42.61.193:5432/finaflow_db"

try:
    print("🔧 Testando importação dos módulos...")
    
    # Importar módulos básicos
    from app.database import engine, Base, create_tables
    print("✅ Módulos básicos importados com sucesso")
    
    # Importar modelos de autenticação
    from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess
    print("✅ Modelos de autenticação importados com sucesso")
    
    # Importar modelos do plano de contas
    from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account
    print("✅ Modelos do plano de contas importados com sucesso")
    
    # Testar criação das tabelas
    print("🔧 Testando criação das tabelas...")
    create_tables()
    print("✅ Tabelas criadas com sucesso")
    
    print("🎉 Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
Script para testar a inicialização do banco de dados
"""

import os
import sys

# Configurar variáveis de ambiente
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.42.61.193:5432/finaflow_db"

try:
    print("🔧 Testando importação dos módulos...")
    
    # Importar módulos básicos
    from app.database import engine, Base, create_tables
    print("✅ Módulos básicos importados com sucesso")
    
    # Importar modelos de autenticação
    from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess
    print("✅ Modelos de autenticação importados com sucesso")
    
    # Importar modelos do plano de contas
    from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account
    print("✅ Modelos do plano de contas importados com sucesso")
    
    # Testar criação das tabelas
    print("🔧 Testando criação das tabelas...")
    create_tables()
    print("✅ Tabelas criadas com sucesso")
    
    print("🎉 Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
Script para testar a inicialização do banco de dados
"""

import os
import sys

# Configurar variáveis de ambiente
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.42.61.193:5432/finaflow_db"

try:
    print("🔧 Testando importação dos módulos...")
    
    # Importar módulos básicos
    from app.database import engine, Base, create_tables
    print("✅ Módulos básicos importados com sucesso")
    
    # Importar modelos de autenticação
    from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess
    print("✅ Modelos de autenticação importados com sucesso")
    
    # Importar modelos do plano de contas
    from app.models.chart_of_accounts import AccountGroup, AccountSubgroup, Account
    print("✅ Modelos do plano de contas importados com sucesso")
    
    # Testar criação das tabelas
    print("🔧 Testando criação das tabelas...")
    create_tables()
    print("✅ Tabelas criadas com sucesso")
    
    print("🎉 Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
