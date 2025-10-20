#!/usr/bin/env python3
"""
Script para criar a tabela de previsões financeiras no banco de dados
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configuração do banco
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finaflow")

def create_forecasts_table():
    """Cria a tabela de previsões financeiras"""
    try:
        # Criar engine
        engine = create_engine(DATABASE_URL)
        
        # Query para criar a tabela
        create_table_query = """
        CREATE TABLE IF NOT EXISTS financial_forecasts (
            id VARCHAR(255) PRIMARY KEY,
            business_unit_id VARCHAR(255) NOT NULL,
            chart_account_id VARCHAR(255) NOT NULL,
            forecast_date DATE NOT NULL,
            amount NUMERIC(15,2) NOT NULL,
            description TEXT,
            forecast_type VARCHAR(50) DEFAULT 'monthly',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Executar criação da tabela
        with engine.connect() as conn:
            conn.execute(text(create_table_query))
            conn.commit()
        
        print("✅ Tabela 'financial_forecasts' criada com sucesso!")
        
        # Criar índices para melhor performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_forecasts_bu ON financial_forecasts(business_unit_id);",
            "CREATE INDEX IF NOT EXISTS idx_forecasts_account ON financial_forecasts(chart_account_id);",
            "CREATE INDEX IF NOT EXISTS idx_forecasts_date ON financial_forecasts(forecast_date);",
            "CREATE INDEX IF NOT EXISTS idx_forecasts_active ON financial_forecasts(is_active);"
        ]
        
        with engine.connect() as conn:
            for index_query in indexes:
                conn.execute(text(index_query))
            conn.commit()
        
        print("✅ Índices criados com sucesso!")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Erro ao criar tabela: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Criando tabela de previsões financeiras...")
    success = create_forecasts_table()
    
    if success:
        print("🎉 Tabela criada com sucesso!")
        sys.exit(0)
    else:
        print("💥 Falha ao criar tabela!")
        sys.exit(1)
