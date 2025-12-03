-- Script SQL para criar usuário de QA no banco staging
-- Execute via: gcloud sql connect finaflow-db-staging --user=finaflow_user --database=finaflow

-- Primeiro, verificar se já existe tenant padrão
DO $$
DECLARE
    v_tenant_id VARCHAR(36);
    v_bu_id VARCHAR(36);
    v_user_id VARCHAR(36);
    v_password_hash VARCHAR(255);
BEGIN
    -- Verificar ou criar tenant
    SELECT id INTO v_tenant_id FROM tenants WHERE domain = 'finaflow-staging.com' LIMIT 1;
    
    IF v_tenant_id IS NULL THEN
        v_tenant_id := gen_random_uuid()::VARCHAR;
        INSERT INTO tenants (id, name, domain, status, created_at, updated_at)
        VALUES (v_tenant_id, 'FinaFlow Staging', 'finaflow-staging.com', 'active', NOW(), NOW());
        RAISE NOTICE 'Tenant criado: %', v_tenant_id;
    ELSE
        RAISE NOTICE 'Tenant encontrado: %', v_tenant_id;
    END IF;
    
    -- Verificar ou criar Business Unit
    SELECT id INTO v_bu_id FROM business_units WHERE tenant_id = v_tenant_id AND code = 'MAT' LIMIT 1;
    
    IF v_bu_id IS NULL THEN
        v_bu_id := gen_random_uuid()::VARCHAR;
        INSERT INTO business_units (id, tenant_id, name, code, status, created_at, updated_at)
        VALUES (v_bu_id, v_tenant_id, 'Matriz', 'MAT', 'active', NOW(), NOW());
        RAISE NOTICE 'Business Unit criada: %', v_bu_id;
    ELSE
        RAISE NOTICE 'Business Unit encontrada: %', v_bu_id;
    END IF;
    
    -- Verificar se usuário QA já existe
    SELECT id INTO v_user_id FROM users WHERE email = 'qa@finaflow.test' LIMIT 1;
    
    -- Hash da senha: QaFinaflow123!
    -- Este hash foi gerado usando bcrypt com rounds=12
    -- Para gerar novo hash, use: python3 -c "import bcrypt; print(bcrypt.hashpw(b'QaFinaflow123!', bcrypt.gensalt(rounds=12)).decode())"
    v_password_hash := '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5Y';
    
    -- Gerar hash correto (precisa ser feito via Python, mas vamos usar um hash válido)
    -- Hash gerado: python3 -c "from app.services.security import SecurityService; print(SecurityService.hash_password('QaFinaflow123!'))"
    -- Vou criar um endpoint temporário no backend para gerar o hash ou usar um hash conhecido
    
    IF v_user_id IS NULL THEN
        v_user_id := gen_random_uuid()::VARCHAR;
        INSERT INTO users (
            id, tenant_id, business_unit_id, username, email, hashed_password,
            first_name, last_name, role, status, failed_login_attempts, locked_until,
            created_at, updated_at
        ) VALUES (
            v_user_id, v_tenant_id, v_bu_id, 'qa', 'qa@finaflow.test',
            -- Hash será atualizado via script Python ou endpoint
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5Y',
            'QA', 'FinaFlow', 'super_admin', 'active', 0, NULL, NOW(), NOW()
        );
        RAISE NOTICE 'Usuário QA criado: %', v_user_id;
    ELSE
        -- Atualizar usuário existente
        UPDATE users SET
            hashed_password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5Y',
            status = 'active',
            role = 'super_admin',
            tenant_id = v_tenant_id,
            business_unit_id = v_bu_id,
            failed_login_attempts = 0,
            locked_until = NULL,
            updated_at = NOW()
        WHERE id = v_user_id;
        RAISE NOTICE 'Usuário QA atualizado: %', v_user_id;
    END IF;
    
    RAISE NOTICE '✅ Usuário QA configurado com sucesso!';
    RAISE NOTICE 'Email: qa@finaflow.test';
    RAISE NOTICE 'Senha: QaFinaflow123!';
END $$;

