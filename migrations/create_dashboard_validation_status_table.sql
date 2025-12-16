-- Migration: Criar tabela de status de validação do dashboard
-- Data: 2025-12-15
-- Descrição: Tabela para rastrear o status da última validação do dashboard contra a planilha do cliente

CREATE TABLE IF NOT EXISTS dashboard_validation_status (
    id VARCHAR(36) PRIMARY KEY,
    
    -- Vinculação com tenant e business unit
    tenant_id VARCHAR(36) NOT NULL,
    business_unit_id VARCHAR(36) NOT NULL,
    
    -- Status da validação (SUCCESS, FAILED, PENDING)
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    
    -- Ano validado
    year VARCHAR(4) NOT NULL,
    
    -- Detalhes da validação (JSON)
    last_validation_at TIMESTAMP NULL,
    validation_details TEXT NULL,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_validation_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    CONSTRAINT fk_validation_business_unit FOREIGN KEY (business_unit_id) REFERENCES business_units(id),
    
    -- Constraint: uma validação por tenant/bu/ano
    CONSTRAINT uq_validation_tenant_bu_year UNIQUE (tenant_id, business_unit_id, year)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_validation_tenant_bu ON dashboard_validation_status(tenant_id, business_unit_id);
CREATE INDEX IF NOT EXISTS idx_validation_year ON dashboard_validation_status(year);
CREATE INDEX IF NOT EXISTS idx_validation_status ON dashboard_validation_status(status);

-- Comentários
COMMENT ON TABLE dashboard_validation_status IS 'Armazena o status da última validação do dashboard contra a planilha do cliente';
COMMENT ON COLUMN dashboard_validation_status.status IS 'Status da validação: SUCCESS, FAILED ou PENDING';
COMMENT ON COLUMN dashboard_validation_status.validation_details IS 'JSON com detalhes da validação (mismatches, estatísticas, etc.)';

