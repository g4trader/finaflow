-- =====================================================================
-- Migration: Corrigir constraints únicos para incluir tenant_id
-- Data: 2025-10-20
-- Objetivo: Permitir códigos duplicados entre diferentes tenants
-- =====================================================================

BEGIN;

-- 1. CHART_ACCOUNT_GROUPS
-- Remover constraint antiga (apenas code)
ALTER TABLE chart_account_groups DROP CONSTRAINT IF EXISTS chart_account_groups_code_key;

-- Adicionar novo constraint (code + tenant_id)
-- IMPORTANTE: NULL = NULL retorna NULL em SQL, então precisamos de índice parcial
CREATE UNIQUE INDEX chart_account_groups_code_tenant_idx 
    ON chart_account_groups (code, tenant_id) 
    WHERE tenant_id IS NOT NULL;

-- Para códigos globais (tenant_id = NULL), manter único por code
CREATE UNIQUE INDEX chart_account_groups_code_global_idx 
    ON chart_account_groups (code) 
    WHERE tenant_id IS NULL;

-- 2. CHART_ACCOUNT_SUBGROUPS
ALTER TABLE chart_account_subgroups DROP CONSTRAINT IF EXISTS chart_account_subgroups_code_key;

CREATE UNIQUE INDEX chart_account_subgroups_code_tenant_idx 
    ON chart_account_subgroups (code, tenant_id) 
    WHERE tenant_id IS NOT NULL;

CREATE UNIQUE INDEX chart_account_subgroups_code_global_idx 
    ON chart_account_subgroups (code) 
    WHERE tenant_id IS NULL;

-- 3. CHART_ACCOUNTS
ALTER TABLE chart_accounts DROP CONSTRAINT IF EXISTS chart_accounts_code_key;

CREATE UNIQUE INDEX chart_accounts_code_tenant_idx 
    ON chart_accounts (code, tenant_id) 
    WHERE tenant_id IS NOT NULL;

CREATE UNIQUE INDEX chart_accounts_code_global_idx 
    ON chart_accounts (code) 
    WHERE tenant_id IS NULL;

COMMIT;

-- Verificar constraints
SELECT 
    tablename, 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename IN ('chart_account_groups', 'chart_account_subgroups', 'chart_accounts')
    AND indexname LIKE '%code%'
ORDER BY tablename, indexname;

