-- =====================================================================
-- Migration: Converter tenant_id de VARCHAR para UUID
-- Data: 2025-10-20
-- Objetivo: Corrigir incompatibilidade de tipos
-- =====================================================================

BEGIN;

-- 1. Chart Account Groups
ALTER TABLE chart_account_groups 
    ALTER COLUMN tenant_id TYPE UUID USING tenant_id::uuid;

-- 2. Chart Account Subgroups
ALTER TABLE chart_account_subgroups 
    ALTER COLUMN tenant_id TYPE UUID USING tenant_id::uuid;

-- 3. Chart Accounts
ALTER TABLE chart_accounts 
    ALTER COLUMN tenant_id TYPE UUID USING tenant_id::uuid;

-- 4. Financial Forecasts
ALTER TABLE financial_forecasts 
    ALTER COLUMN tenant_id TYPE UUID USING tenant_id::uuid;

COMMIT;

-- Verificar tipos
SELECT 
    'chart_account_groups' as tabela,
    data_type 
FROM information_schema.columns 
WHERE table_name = 'chart_account_groups' 
    AND column_name = 'tenant_id'
UNION ALL
SELECT 
    'chart_account_subgroups',
    data_type 
FROM information_schema.columns 
WHERE table_name = 'chart_account_subgroups' 
    AND column_name = 'tenant_id'
UNION ALL
SELECT 
    'chart_accounts',
    data_type 
FROM information_schema.columns 
WHERE table_name = 'chart_accounts' 
    AND column_name = 'tenant_id'
UNION ALL
SELECT 
    'financial_forecasts',
    data_type 
FROM information_schema.columns 
WHERE table_name = 'financial_forecasts' 
    AND column_name = 'tenant_id';

