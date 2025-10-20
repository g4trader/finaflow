-- Migration: Criar tabela de lançamentos diários
-- Data: 2025-10-20
-- Descrição: Criar tabela que espelha exatamente a estrutura da planilha

CREATE TABLE IF NOT EXISTS lancamentos_diarios (
    id VARCHAR(36) PRIMARY KEY,
    
    -- Campos obrigatórios da planilha
    data_movimentacao TIMESTAMP NOT NULL,
    valor DECIMAL(15,2) NOT NULL,
    liquidacao TIMESTAMP NULL,
    observacoes TEXT NULL,
    
    -- Campos obrigatórios vinculados ao plano de contas
    conta_id VARCHAR(36) NOT NULL,
    subgrupo_id VARCHAR(36) NOT NULL,
    grupo_id VARCHAR(36) NOT NULL,
    
    -- Tipo de transação baseado no Grupo
    transaction_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pendente',
    
    -- Vinculação com empresa/BU
    tenant_id VARCHAR(36) NOT NULL,
    business_unit_id VARCHAR(36) NOT NULL,
    
    -- Usuário que criou
    created_by VARCHAR(36) NOT NULL,
    
    -- Metadados
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_lancamentos_conta FOREIGN KEY (conta_id) REFERENCES chart_accounts(id),
    CONSTRAINT fk_lancamentos_subgrupo FOREIGN KEY (subgrupo_id) REFERENCES chart_account_subgroups(id),
    CONSTRAINT fk_lancamentos_grupo FOREIGN KEY (grupo_id) REFERENCES chart_account_groups(id),
    CONSTRAINT fk_lancamentos_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    CONSTRAINT fk_lancamentos_business_unit FOREIGN KEY (business_unit_id) REFERENCES business_units(id),
    CONSTRAINT fk_lancamentos_user FOREIGN KEY (created_by) REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT uq_lancamento_data_conta_valor UNIQUE (data_movimentacao, conta_id, valor, tenant_id, business_unit_id),
    CONSTRAINT chk_valor_positivo CHECK (valor > 0)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_lancamentos_tenant_bu ON lancamentos_diarios(tenant_id, business_unit_id);
CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON lancamentos_diarios(data_movimentacao);
CREATE INDEX IF NOT EXISTS idx_lancamentos_conta ON lancamentos_diarios(conta_id);
CREATE INDEX IF NOT EXISTS idx_lancamentos_subgrupo ON lancamentos_diarios(subgrupo_id);
CREATE INDEX IF NOT EXISTS idx_lancamentos_grupo ON lancamentos_diarios(grupo_id);
CREATE INDEX IF NOT EXISTS idx_lancamentos_type ON lancamentos_diarios(transaction_type);
CREATE INDEX IF NOT EXISTS idx_lancamentos_active ON lancamentos_diarios(is_active);

-- Comentários para documentação
COMMENT ON TABLE lancamentos_diarios IS 'Lançamentos diários - espelho exato da planilha';
COMMENT ON COLUMN lancamentos_diarios.data_movimentacao IS 'Data Movimentação da planilha';
COMMENT ON COLUMN lancamentos_diarios.valor IS 'Valor da planilha';
COMMENT ON COLUMN lancamentos_diarios.liquidacao IS 'Liquidação da planilha';
COMMENT ON COLUMN lancamentos_diarios.observacoes IS 'Observações da planilha';
COMMENT ON COLUMN lancamentos_diarios.conta_id IS 'Conta (obrigatório - link com plano de contas)';
COMMENT ON COLUMN lancamentos_diarios.subgrupo_id IS 'Subgrupo (obrigatório - link com plano de contas)';
COMMENT ON COLUMN lancamentos_diarios.grupo_id IS 'Grupo (obrigatório - link com plano de contas)';
COMMENT ON COLUMN lancamentos_diarios.transaction_type IS 'Tipo calculado automaticamente baseado no grupo';
