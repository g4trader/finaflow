-- Migration: Adicionar coluna liquidation_account_id à tabela lancamentos_diarios
-- Data: 2025-01-XX
-- Descrição: Adiciona campo para associar lançamentos diários com contas de liquidação (scb, cef, cx, etc.)

-- Adicionar coluna se não existir
ALTER TABLE lancamentos_diarios 
ADD COLUMN IF NOT EXISTS liquidation_account_id VARCHAR(36);

-- Adicionar foreign key se não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_lancamentos_diarios_liquidation_account'
    ) THEN
        ALTER TABLE lancamentos_diarios
        ADD CONSTRAINT fk_lancamentos_diarios_liquidation_account
        FOREIGN KEY (liquidation_account_id) 
        REFERENCES liquidation_accounts(id);
    END IF;
END $$;

-- Criar índice para performance
CREATE INDEX IF NOT EXISTS idx_lancamentos_diarios_liquidation_account 
ON lancamentos_diarios(liquidation_account_id);

