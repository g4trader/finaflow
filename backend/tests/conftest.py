"""
Configuração global de testes pytest
Mocka o database antes de qualquer import que o use
"""

import sys
from unittest.mock import MagicMock

# Mock do database antes de qualquer import
mock_database = MagicMock()
mock_database.SessionLocal = MagicMock()
mock_database.get_db = MagicMock()
sys.modules['app.database'] = mock_database

# Configurar variável de ambiente para evitar tentativa de conexão
import os
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
