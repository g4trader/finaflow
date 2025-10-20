-- ============================================================================
-- MIGRATION: Adicionar tenant_id ao Plano de Contas
-- Data: 2025-10-19
-- Objetivo: Garantir isolamento multi-tenant completo
-- ============================================================================

-- Passo 1: Adicionar coluna tenant_id às tabelas do plano de contas
-- ============================================================================

-- 1.1 Adicionar tenant_id a chart_account_groups
ALTER TABLE chart_account_groups 
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);

-- 1.2 Adicionar tenant_id a chart_account_subgroups
ALTER TABLE chart_account_subgroups 
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);

-- 1.3 Adicionar tenant_id a chart_accounts
ALTER TABLE chart_accounts 
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);

-- 1.4 Adicionar tenant_id a financial_forecasts (se não existir)
ALTER TABLE financial_forecasts 
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);

-- ============================================================================
-- Passo 2: Atualizar dados existentes com tenant_id do tenant padrão
-- ============================================================================

-- 2.1 Obter ID do tenant padrão (assumindo que é o primeiro/único)
DO $$
DECLARE
    default_tenant_id VARCHAR(36);
BEGIN
    -- Buscar o primeiro tenant (ou o tenant 'FINAFlow')
    SELECT id INTO default_tenant_id 
    FROM tenants 
    WHERE name = 'FINAFlow' OR name LIKE '%FINAFlow%'
    LIMIT 1;
    
    -- Se não encontrar, pegar o primeiro tenant qualquer
    IF default_tenant_id IS NULL THEN
        SELECT id INTO default_tenant_id 
        FROM tenants 
        ORDER BY created_at 
        LIMIT 1;
    END IF;
    
    -- Se ainda assim não tiver tenant, criar um padrão
    IF default_tenant_id IS NULL THEN
        INSERT INTO tenants (id, name, domain, status, created_at, updated_at)
        VALUES (
            gen_random_uuid()::text,
            'FINAFlow',
            'finaflow.com',
            'active',
            NOW(),
            NOW()
        )
        RETURNING id INTO default_tenant_id;
        
        RAISE NOTICE 'Tenant padrão criado: %', default_tenant_id;
    END IF;
    
    RAISE NOTICE 'Usando tenant_id: %', default_tenant_id;
    
    -- 2.2 Atualizar chart_account_groups
    UPDATE chart_account_groups
    SET tenant_id = default_tenant_id
    WHERE tenant_id IS NULL;
    
    RAISE NOTICE 'Grupos atualizados: %', (SELECT COUNT(*) FROM chart_account_groups WHERE tenant_id = default_tenant_id);
    
    -- 2.3 Atualizar chart_account_subgroups
    UPDATE chart_account_subgroups
    SET tenant_id = default_tenant_id
    WHERE tenant_id IS NULL;
    
    RAISE NOTICE 'Subgrupos atualizados: %', (SELECT COUNT(*) FROM chart_account_subgroups WHERE tenant_id = default_tenant_id);
    
    -- 2.4 Atualizar chart_accounts
    UPDATE chart_accounts
    SET tenant_id = default_tenant_id
    WHERE tenant_id IS NULL;
    
    RAISE NOTICE 'Contas atualizadas: %', (SELECT COUNT(*) FROM chart_accounts WHERE tenant_id = default_tenant_id);
    
    -- 2.5 Atualizar financial_forecasts
    UPDATE financial_forecasts
    SET tenant_id = default_tenant_id
    WHERE tenant_id IS NULL;
    
    RAISE NOTICE 'Previsões atualizadas: %', (SELECT COUNT(*) FROM financial_forecasts WHERE tenant_id = default_tenant_id);
END $$;

-- ============================================================================
-- Passo 3: Adicionar Foreign Keys
-- ============================================================================

-- 3.1 Adicionar FK em chart_account_groups
ALTER TABLE chart_account_groups
DROP CONSTRAINT IF EXISTS fk_chart_account_groups_tenant;

ALTER TABLE chart_account_groups
ADD CONSTRAINT fk_chart_account_groups_tenant
FOREIGN KEY (tenant_id) REFERENCES tenants(id)
ON DELETE CASCADE;

-- 3.2 Adicionar FK em chart_account_subgroups
ALTER TABLE chart_account_subgroups
DROP CONSTRAINT IF EXISTS fk_chart_account_subgroups_tenant;

ALTER TABLE chart_account_subgroups
ADD CONSTRAINT fk_chart_account_subgroups_tenant
FOREIGN KEY (tenant_id) REFERENCES tenants(id)
ON DELETE CASCADE;

-- 3.3 Adicionar FK em chart_accounts
ALTER TABLE chart_accounts
DROP CONSTRAINT IF EXISTS fk_chart_accounts_tenant;

ALTER TABLE chart_accounts
ADD CONSTRAINT fk_chart_accounts_tenant
FOREIGN KEY (tenant_id) REFERENCES tenants(id)
ON DELETE CASCADE;

-- 3.4 Adicionar FK em financial_forecasts
ALTER TABLE financial_forecasts
DROP CONSTRAINT IF EXISTS fk_financial_forecasts_tenant;

ALTER TABLE financial_forecasts
ADD CONSTRAINT fk_financial_forecasts_tenant
FOREIGN KEY (tenant_id) REFERENCES tenants(id)
ON DELETE CASCADE;

-- ============================================================================
-- Passo 4: Atualizar constraints únicos para incluir tenant_id
-- ============================================================================

-- 4.1 Dropar constraint antigo e criar novo para groups
ALTER TABLE chart_account_groups
DROP CONSTRAINT IF EXISTS uq_group_code;

ALTER TABLE chart_account_groups
DROP CONSTRAINT IF EXISTS uq_group_code_tenant;

ALTER TABLE chart_account_groups
ADD CONSTRAINT uq_group_code_tenant 
UNIQUE (code, tenant_id);

-- 4.2 Dropar constraint antigo e criar novo para subgroups
ALTER TABLE chart_account_subgroups
DROP CONSTRAINT IF EXISTS uq_subgroup_code_group;

ALTER TABLE chart_account_subgroups
DROP CONSTRAINT IF EXISTS uq_subgroup_code_group_tenant;

ALTER TABLE chart_account_subgroups
ADD CONSTRAINT uq_subgroup_code_group_tenant 
UNIQUE (code, group_id, tenant_id);

-- 4.3 Dropar constraint antigo e criar novo para accounts
ALTER TABLE chart_accounts
DROP CONSTRAINT IF EXISTS uq_account_code_subgroup;

ALTER TABLE chart_accounts
DROP CONSTRAINT IF EXISTS uq_account_code_subgroup_tenant;

ALTER TABLE chart_accounts
ADD CONSTRAINT uq_account_code_subgroup_tenant 
UNIQUE (code, subgroup_id, tenant_id);

-- ============================================================================
-- Passo 5: Criar índices para performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_chart_account_groups_tenant 
ON chart_account_groups(tenant_id);

CREATE INDEX IF NOT EXISTS idx_chart_account_subgroups_tenant 
ON chart_account_subgroups(tenant_id);

CREATE INDEX IF NOT EXISTS idx_chart_accounts_tenant 
ON chart_accounts(tenant_id);

CREATE INDEX IF NOT EXISTS idx_financial_forecasts_tenant 
ON financial_forecasts(tenant_id);

-- ============================================================================
-- Passo 6: Criar vínculos business_unit_chart_accounts para dados existentes
-- ============================================================================

DO $$
DECLARE
    default_bu_id VARCHAR(36);
    account_record RECORD;
    links_created INT := 0;
BEGIN
    -- Buscar a primeira Business Unit
    SELECT id INTO default_bu_id 
    FROM business_units 
    ORDER BY created_at 
    LIMIT 1;
    
    IF default_bu_id IS NOT NULL THEN
        RAISE NOTICE 'Criando vínculos para BU: %', default_bu_id;
        
        -- Para cada conta existente, criar vínculo com a BU
        FOR account_record IN (
            SELECT id FROM chart_accounts WHERE is_active = true
        ) LOOP
            -- Inserir vínculo se não existir
            INSERT INTO business_unit_chart_accounts (
                id,
                business_unit_id,
                chart_account_id,
                is_custom,
                is_active,
                created_at,
                updated_at
            )
            SELECT 
                gen_random_uuid()::text,
                default_bu_id,
                account_record.id,
                false,
                true,
                NOW(),
                NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM business_unit_chart_accounts
                WHERE business_unit_id = default_bu_id 
                AND chart_account_id = account_record.id
            );
            
            links_created := links_created + 1;
        END LOOP;
        
        RAISE NOTICE 'Vínculos BU-Conta criados: %', links_created;
    ELSE
        RAISE NOTICE 'Nenhuma Business Unit encontrada - vínculos não criados';
    END IF;
END $$;

-- ============================================================================
-- Passo 7: Verificação final
-- ============================================================================

DO $$
DECLARE
    grupos_count INT;
    subgrupos_count INT;
    contas_count INT;
    vinculos_count INT;
    grupos_com_tenant INT;
    contas_com_tenant INT;
BEGIN
    -- Contar registros
    SELECT COUNT(*) INTO grupos_count FROM chart_account_groups;
    SELECT COUNT(*) INTO subgrupos_count FROM chart_account_subgroups;
    SELECT COUNT(*) INTO contas_count FROM chart_accounts;
    SELECT COUNT(*) INTO vinculos_count FROM business_unit_chart_accounts;
    
    -- Contar com tenant_id
    SELECT COUNT(*) INTO grupos_com_tenant FROM chart_account_groups WHERE tenant_id IS NOT NULL;
    SELECT COUNT(*) INTO contas_com_tenant FROM chart_accounts WHERE tenant_id IS NOT NULL;
    
    -- Relatório
    RAISE NOTICE '============================================';
    RAISE NOTICE 'RESUMO DA MIGRATION';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Grupos: % (com tenant: %)', grupos_count, grupos_com_tenant;
    RAISE NOTICE 'Subgrupos: %', subgrupos_count;
    RAISE NOTICE 'Contas: % (com tenant: %)', contas_count, contas_com_tenant;
    RAISE NOTICE 'Vínculos BU-Conta: %', vinculos_count;
    RAISE NOTICE '============================================';
    
    -- Validação
    IF grupos_com_tenant = grupos_count AND contas_com_tenant = contas_count THEN
        RAISE NOTICE '✅ MIGRATION CONCLUÍDA COM SUCESSO!';
    ELSE
        RAISE WARNING '⚠️ Alguns registros ainda sem tenant_id';
    END IF;
END $$;

-- ============================================================================
-- FIM DA MIGRATION
-- ============================================================================

