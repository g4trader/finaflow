#!/usr/bin/env python3
"""
Script simples para testar se o hybrid_app.py consegue ser executado
"""

import sys
import os

# Simular as dependências que não estão instaladas
class MockFastAPI:
    def __init__(self, title="Test", version="1.0"):
        self.title = title
        self.version = version
    
    def add_middleware(self, *args, **kwargs):
        pass
    
    def get(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def post(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def put(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def delete(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MockHTTPException:
    pass

class MockDepends:
    pass

class MockCORSMiddleware:
    pass

class MockHTTPBearer:
    pass

class MockBaseModel:
    metadata = type('metadata', (), {})()
    __tablename__ = "mock_table"

class MockSession:
    pass

# Mock das dependências
sys.modules['fastapi'] = type('fastapi', (), {
    'FastAPI': MockFastAPI,
    'HTTPException': MockHTTPException,
    'Depends': MockDepends,
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['fastapi.security'] = type('fastapi.security', (), {
    'HTTPBearer': MockHTTPBearer
})

sys.modules['fastapi.middleware.cors'] = type('fastapi.middleware.cors', (), {
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['pydantic'] = type('pydantic', (), {
    'BaseModel': MockBaseModel
})

sys.modules['sqlalchemy.orm'] = type('sqlalchemy.orm', (), {
    'Session': MockSession
})

sys.modules['uvicorn'] = type('uvicorn', (), {
    'run': lambda app, host="0.0.0.0", port=8080: print(f"Mock uvicorn.run({app}, host={host}, port={port})")
})

sys.modules['jwt'] = type('jwt', (), {})
sys.modules['datetime'] = type('datetime', (), {})
class MockOptional:
    def __getitem__(self, item):
        return item

sys.modules['typing'] = type('typing', (), {
    'List': list,
    'Optional': MockOptional()
})

# Mock dos módulos locais
sys.modules['app.database'] = type('app.database', (), {
    'get_db': lambda: None,
    'engine': None
})

sys.modules['app.models.auth'] = type('app.models.auth', (), {
    'User': MockBaseModel,
    'Tenant': MockBaseModel,
    'BusinessUnit': MockBaseModel,
    'UserTenantAccess': MockBaseModel,
    'UserBusinessUnitAccess': MockBaseModel,
    'Base': MockBaseModel
})

sys.modules['app.models.chart_of_accounts'] = type('app.models.chart_of_accounts', (), {
    'AccountGroup': MockBaseModel,
    'AccountSubgroup': MockBaseModel,
    'Account': MockBaseModel,
    'AccountGroupCreate': MockBaseModel,
    'AccountGroupUpdate': MockBaseModel,
    'AccountGroupResponse': MockBaseModel,
    'AccountSubgroupCreate': MockBaseModel,
    'AccountSubgroupUpdate': MockBaseModel,
    'AccountSubgroupResponse': MockBaseModel,
    'AccountCreate': MockBaseModel,
    'AccountUpdate': MockBaseModel,
    'AccountResponse': MockBaseModel
})

try:
    print("Tentando executar hybrid_app.py...")
    exec(open('hybrid_app.py').read())
    print("✅ Execução bem-sucedida!")
except Exception as e:
    print(f"❌ Erro na execução: {e}")
    import traceback
    traceback.print_exc()

Script simples para testar se o hybrid_app.py consegue ser executado
"""

import sys
import os

# Simular as dependências que não estão instaladas
class MockFastAPI:
    def __init__(self, title="Test", version="1.0"):
        self.title = title
        self.version = version
    
    def add_middleware(self, *args, **kwargs):
        pass
    
    def get(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def post(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def put(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def delete(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MockHTTPException:
    pass

class MockDepends:
    pass

class MockCORSMiddleware:
    pass

class MockHTTPBearer:
    pass

class MockBaseModel:
    metadata = type('metadata', (), {})()
    __tablename__ = "mock_table"

class MockSession:
    pass

# Mock das dependências
sys.modules['fastapi'] = type('fastapi', (), {
    'FastAPI': MockFastAPI,
    'HTTPException': MockHTTPException,
    'Depends': MockDepends,
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['fastapi.security'] = type('fastapi.security', (), {
    'HTTPBearer': MockHTTPBearer
})

sys.modules['fastapi.middleware.cors'] = type('fastapi.middleware.cors', (), {
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['pydantic'] = type('pydantic', (), {
    'BaseModel': MockBaseModel
})

sys.modules['sqlalchemy.orm'] = type('sqlalchemy.orm', (), {
    'Session': MockSession
})

sys.modules['uvicorn'] = type('uvicorn', (), {
    'run': lambda app, host="0.0.0.0", port=8080: print(f"Mock uvicorn.run({app}, host={host}, port={port})")
})

sys.modules['jwt'] = type('jwt', (), {})
sys.modules['datetime'] = type('datetime', (), {})
class MockOptional:
    def __getitem__(self, item):
        return item

sys.modules['typing'] = type('typing', (), {
    'List': list,
    'Optional': MockOptional()
})

# Mock dos módulos locais
sys.modules['app.database'] = type('app.database', (), {
    'get_db': lambda: None,
    'engine': None
})

sys.modules['app.models.auth'] = type('app.models.auth', (), {
    'User': MockBaseModel,
    'Tenant': MockBaseModel,
    'BusinessUnit': MockBaseModel,
    'UserTenantAccess': MockBaseModel,
    'UserBusinessUnitAccess': MockBaseModel,
    'Base': MockBaseModel
})

sys.modules['app.models.chart_of_accounts'] = type('app.models.chart_of_accounts', (), {
    'AccountGroup': MockBaseModel,
    'AccountSubgroup': MockBaseModel,
    'Account': MockBaseModel,
    'AccountGroupCreate': MockBaseModel,
    'AccountGroupUpdate': MockBaseModel,
    'AccountGroupResponse': MockBaseModel,
    'AccountSubgroupCreate': MockBaseModel,
    'AccountSubgroupUpdate': MockBaseModel,
    'AccountSubgroupResponse': MockBaseModel,
    'AccountCreate': MockBaseModel,
    'AccountUpdate': MockBaseModel,
    'AccountResponse': MockBaseModel
})

try:
    print("Tentando executar hybrid_app.py...")
    exec(open('hybrid_app.py').read())
    print("✅ Execução bem-sucedida!")
except Exception as e:
    print(f"❌ Erro na execução: {e}")
    import traceback
    traceback.print_exc()

Script simples para testar se o hybrid_app.py consegue ser executado
"""

import sys
import os

# Simular as dependências que não estão instaladas
class MockFastAPI:
    def __init__(self, title="Test", version="1.0"):
        self.title = title
        self.version = version
    
    def add_middleware(self, *args, **kwargs):
        pass
    
    def get(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def post(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def put(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def delete(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MockHTTPException:
    pass

class MockDepends:
    pass

class MockCORSMiddleware:
    pass

class MockHTTPBearer:
    pass

class MockBaseModel:
    metadata = type('metadata', (), {})()
    __tablename__ = "mock_table"

class MockSession:
    pass

# Mock das dependências
sys.modules['fastapi'] = type('fastapi', (), {
    'FastAPI': MockFastAPI,
    'HTTPException': MockHTTPException,
    'Depends': MockDepends,
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['fastapi.security'] = type('fastapi.security', (), {
    'HTTPBearer': MockHTTPBearer
})

sys.modules['fastapi.middleware.cors'] = type('fastapi.middleware.cors', (), {
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['pydantic'] = type('pydantic', (), {
    'BaseModel': MockBaseModel
})

sys.modules['sqlalchemy.orm'] = type('sqlalchemy.orm', (), {
    'Session': MockSession
})

sys.modules['uvicorn'] = type('uvicorn', (), {
    'run': lambda app, host="0.0.0.0", port=8080: print(f"Mock uvicorn.run({app}, host={host}, port={port})")
})

sys.modules['jwt'] = type('jwt', (), {})
sys.modules['datetime'] = type('datetime', (), {})
class MockOptional:
    def __getitem__(self, item):
        return item

sys.modules['typing'] = type('typing', (), {
    'List': list,
    'Optional': MockOptional()
})

# Mock dos módulos locais
sys.modules['app.database'] = type('app.database', (), {
    'get_db': lambda: None,
    'engine': None
})

sys.modules['app.models.auth'] = type('app.models.auth', (), {
    'User': MockBaseModel,
    'Tenant': MockBaseModel,
    'BusinessUnit': MockBaseModel,
    'UserTenantAccess': MockBaseModel,
    'UserBusinessUnitAccess': MockBaseModel,
    'Base': MockBaseModel
})

sys.modules['app.models.chart_of_accounts'] = type('app.models.chart_of_accounts', (), {
    'AccountGroup': MockBaseModel,
    'AccountSubgroup': MockBaseModel,
    'Account': MockBaseModel,
    'AccountGroupCreate': MockBaseModel,
    'AccountGroupUpdate': MockBaseModel,
    'AccountGroupResponse': MockBaseModel,
    'AccountSubgroupCreate': MockBaseModel,
    'AccountSubgroupUpdate': MockBaseModel,
    'AccountSubgroupResponse': MockBaseModel,
    'AccountCreate': MockBaseModel,
    'AccountUpdate': MockBaseModel,
    'AccountResponse': MockBaseModel
})

try:
    print("Tentando executar hybrid_app.py...")
    exec(open('hybrid_app.py').read())
    print("✅ Execução bem-sucedida!")
except Exception as e:
    print(f"❌ Erro na execução: {e}")
    import traceback
    traceback.print_exc()

Script simples para testar se o hybrid_app.py consegue ser executado
"""

import sys
import os

# Simular as dependências que não estão instaladas
class MockFastAPI:
    def __init__(self, title="Test", version="1.0"):
        self.title = title
        self.version = version
    
    def add_middleware(self, *args, **kwargs):
        pass
    
    def get(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def post(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def put(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def delete(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MockHTTPException:
    pass

class MockDepends:
    pass

class MockCORSMiddleware:
    pass

class MockHTTPBearer:
    pass

class MockBaseModel:
    metadata = type('metadata', (), {})()
    __tablename__ = "mock_table"

class MockSession:
    pass

# Mock das dependências
sys.modules['fastapi'] = type('fastapi', (), {
    'FastAPI': MockFastAPI,
    'HTTPException': MockHTTPException,
    'Depends': MockDepends,
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['fastapi.security'] = type('fastapi.security', (), {
    'HTTPBearer': MockHTTPBearer
})

sys.modules['fastapi.middleware.cors'] = type('fastapi.middleware.cors', (), {
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['pydantic'] = type('pydantic', (), {
    'BaseModel': MockBaseModel
})

sys.modules['sqlalchemy.orm'] = type('sqlalchemy.orm', (), {
    'Session': MockSession
})

sys.modules['uvicorn'] = type('uvicorn', (), {
    'run': lambda app, host="0.0.0.0", port=8080: print(f"Mock uvicorn.run({app}, host={host}, port={port})")
})

sys.modules['jwt'] = type('jwt', (), {})
sys.modules['datetime'] = type('datetime', (), {})
class MockOptional:
    def __getitem__(self, item):
        return item

sys.modules['typing'] = type('typing', (), {
    'List': list,
    'Optional': MockOptional()
})

# Mock dos módulos locais
sys.modules['app.database'] = type('app.database', (), {
    'get_db': lambda: None,
    'engine': None
})

sys.modules['app.models.auth'] = type('app.models.auth', (), {
    'User': MockBaseModel,
    'Tenant': MockBaseModel,
    'BusinessUnit': MockBaseModel,
    'UserTenantAccess': MockBaseModel,
    'UserBusinessUnitAccess': MockBaseModel,
    'Base': MockBaseModel
})

sys.modules['app.models.chart_of_accounts'] = type('app.models.chart_of_accounts', (), {
    'AccountGroup': MockBaseModel,
    'AccountSubgroup': MockBaseModel,
    'Account': MockBaseModel,
    'AccountGroupCreate': MockBaseModel,
    'AccountGroupUpdate': MockBaseModel,
    'AccountGroupResponse': MockBaseModel,
    'AccountSubgroupCreate': MockBaseModel,
    'AccountSubgroupUpdate': MockBaseModel,
    'AccountSubgroupResponse': MockBaseModel,
    'AccountCreate': MockBaseModel,
    'AccountUpdate': MockBaseModel,
    'AccountResponse': MockBaseModel
})

try:
    print("Tentando executar hybrid_app.py...")
    exec(open('hybrid_app.py').read())
    print("✅ Execução bem-sucedida!")
except Exception as e:
    print(f"❌ Erro na execução: {e}")
    import traceback
    traceback.print_exc()

Script simples para testar se o hybrid_app.py consegue ser executado
"""

import sys
import os

# Simular as dependências que não estão instaladas
class MockFastAPI:
    def __init__(self, title="Test", version="1.0"):
        self.title = title
        self.version = version
    
    def add_middleware(self, *args, **kwargs):
        pass
    
    def get(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def post(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def put(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def delete(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MockHTTPException:
    pass

class MockDepends:
    pass

class MockCORSMiddleware:
    pass

class MockHTTPBearer:
    pass

class MockBaseModel:
    metadata = type('metadata', (), {})()
    __tablename__ = "mock_table"

class MockSession:
    pass

# Mock das dependências
sys.modules['fastapi'] = type('fastapi', (), {
    'FastAPI': MockFastAPI,
    'HTTPException': MockHTTPException,
    'Depends': MockDepends,
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['fastapi.security'] = type('fastapi.security', (), {
    'HTTPBearer': MockHTTPBearer
})

sys.modules['fastapi.middleware.cors'] = type('fastapi.middleware.cors', (), {
    'CORSMiddleware': MockCORSMiddleware
})

sys.modules['pydantic'] = type('pydantic', (), {
    'BaseModel': MockBaseModel
})

sys.modules['sqlalchemy.orm'] = type('sqlalchemy.orm', (), {
    'Session': MockSession
})

sys.modules['uvicorn'] = type('uvicorn', (), {
    'run': lambda app, host="0.0.0.0", port=8080: print(f"Mock uvicorn.run({app}, host={host}, port={port})")
})

sys.modules['jwt'] = type('jwt', (), {})
sys.modules['datetime'] = type('datetime', (), {})
class MockOptional:
    def __getitem__(self, item):
        return item

sys.modules['typing'] = type('typing', (), {
    'List': list,
    'Optional': MockOptional()
})

# Mock dos módulos locais
sys.modules['app.database'] = type('app.database', (), {
    'get_db': lambda: None,
    'engine': None
})

sys.modules['app.models.auth'] = type('app.models.auth', (), {
    'User': MockBaseModel,
    'Tenant': MockBaseModel,
    'BusinessUnit': MockBaseModel,
    'UserTenantAccess': MockBaseModel,
    'UserBusinessUnitAccess': MockBaseModel,
    'Base': MockBaseModel
})

sys.modules['app.models.chart_of_accounts'] = type('app.models.chart_of_accounts', (), {
    'AccountGroup': MockBaseModel,
    'AccountSubgroup': MockBaseModel,
    'Account': MockBaseModel,
    'AccountGroupCreate': MockBaseModel,
    'AccountGroupUpdate': MockBaseModel,
    'AccountGroupResponse': MockBaseModel,
    'AccountSubgroupCreate': MockBaseModel,
    'AccountSubgroupUpdate': MockBaseModel,
    'AccountSubgroupResponse': MockBaseModel,
    'AccountCreate': MockBaseModel,
    'AccountUpdate': MockBaseModel,
    'AccountResponse': MockBaseModel
})

try:
    print("Tentando executar hybrid_app.py...")
    exec(open('hybrid_app.py').read())
    print("✅ Execução bem-sucedida!")
except Exception as e:
    print(f"❌ Erro na execução: {e}")
    import traceback
    traceback.print_exc()
