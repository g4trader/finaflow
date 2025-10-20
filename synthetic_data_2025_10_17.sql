-- Script SQL para inserir 50 registros sintéticos
-- Data: 17/10/2025
-- 40 pequenos negócios + 10 sociedades
-- Gerado em: 2025-10-18 16:44:51

-- Nota: Você precisa substituir os IDs abaixo pelos IDs reais do seu banco:
-- - tenant_id: ID da empresa/tenant
-- - business_unit_id: ID da unidade de negócio (Matriz)
-- - user_id: ID do usuário admin
-- - chart_account_id: ID de uma conta do plano de contas

-- Exemplo de como obter os IDs:
-- SELECT id FROM tenants WHERE name = 'FinaFlow' LIMIT 1;
-- SELECT id FROM business_units WHERE name = 'Matriz' LIMIT 1;
-- SELECT id FROM users WHERE username = 'admin' LIMIT 1;
-- SELECT id FROM chart_accounts LIMIT 1;

-- Substitua os valores abaixo pelos IDs reais:
-- SET @tenant_id = 'SEU_TENANT_ID_AQUI';
-- SET @business_unit_id = 'SEU_BUSINESS_UNIT_ID_AQUI';
-- SET @user_id = 'SEU_USER_ID_AQUI';
-- SET @chart_account_id = 'SEU_CHART_ACCOUNT_ID_AQUI';

-- Ou use diretamente nos INSERTs abaixo:

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'efe2df54-1201-4eae-87a8-3c5e30baab1e',
    'REF-20251018-5659',
    'Serviços de consultoria - Transação 001',
    794.34,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '77d1bee4-79d9-486d-aabc-8cc3e97f089b',
    'REF-20251018-4362',
    'Material de escritório - Transação 002',
    41.46,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '5ea7ab40-0b35-492a-bada-90a1591797bb',
    'REF-20251018-1885',
    'Serviços de limpeza - Transação 003',
    166.25,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'f06ca6ef-a279-4585-af9e-f99536cf73f4',
    'REF-20251018-8878',
    'Combustível para veículos - Transação 004',
    114.67,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '17b69718-e923-4541-86d0-2420ba5ffe57',
    'REF-20251018-5356',
    'Taxas e impostos - Transação 005',
    184.83,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '7b6cec05-40b6-44cd-9687-fa26e0f9251f',
    'REF-20251018-6111',
    'Combustível para veículos - Transação 006',
    155.14,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '6b3019e1-4b8f-4d56-8af0-e0148dad0028',
    'REF-20251018-4253',
    'Compra de matéria-prima - Transação 007',
    192.02,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '2f0b8f0f-486a-4812-a9b4-a308ff0d874c',
    'REF-20251018-1023',
    'Venda de produtos - Loja - Transação 008',
    318.59,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'bd927abc-4bd5-44a1-a4f3-66220576e5bb',
    'REF-20251018-9943',
    'Aluguel do estabelecimento - Transação 009',
    714.46,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'cf18e821-c77d-42eb-8c1b-e7432033523e',
    'REF-20251018-3951',
    'Marketing e publicidade - Transação 010',
    280.83,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '252349d1-b087-4c08-a1f2-8794f290944d',
    'REF-20251018-9497',
    'Conta de água - Transação 011',
    59.24,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'a8ca3b7f-3bda-40e2-a452-61f70282d590',
    'REF-20251018-2521',
    'Serviços de consultoria - Transação 012',
    126.36,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'b12ca17c-6747-4428-a3f2-765706f8a915',
    'REF-20251018-9447',
    'Venda de produtos - Feira - Transação 013',
    118.41,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '1eafd6a7-416b-4687-81f2-ffcab4c10ca3',
    'REF-20251018-3397',
    'Serviços de entrega - Transação 014',
    80.88,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '630ec3dd-0fbf-40c9-a6aa-afeb74230809',
    'REF-20251018-9413',
    'Conta de energia elétrica - Transação 015',
    102.7,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'c8762f4e-21c9-4d73-9441-77737ce83d53',
    'REF-20251018-8288',
    'Venda de produtos online - Transação 016',
    89.01,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '68d6a62d-bcca-44af-9621-0294c48bfa61',
    'REF-20251018-5654',
    'Conta de água - Transação 017',
    66.84,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'ad2a5c70-73b8-43cd-a23f-fba7e98de44c',
    'REF-20251018-9994',
    'Serviços de manutenção - Transação 018',
    234.54,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'ffade9a8-6145-4e70-9902-e24e151bb093',
    'REF-20251018-8119',
    'Combustível para veículos - Transação 019',
    90.62,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '2e6c4bef-8faa-43ba-91dd-054b07e8c444',
    'REF-20251018-7893',
    'Conta de água - Transação 020',
    99.1,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '00925fd6-8740-4015-9d41-b401d4004642',
    'REF-20251018-2246',
    'Conta de água - Transação 021',
    60.06,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'bb4530d6-94c9-4d98-be26-9933bb4b857f',
    'REF-20251018-1814',
    'Compra de matéria-prima - Transação 022',
    191.19,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '38631c0e-b69d-402d-bf31-e8b27dee7e7f',
    'REF-20251018-4296',
    'Conta de água - Transação 023',
    70.03,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '251f422a-d1fe-4489-9d91-1233354436e7',
    'REF-20251018-9799',
    'Serviços de entrega - Transação 024',
    75.23,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '31c84a37-9698-412d-a152-55f322ddfd7b',
    'REF-20251018-4779',
    'Conta de energia elétrica - Transação 025',
    125.27,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'e565b0e6-986e-4731-bdec-ce9f0960ff1f',
    'REF-20251018-7646',
    'Compra de matéria-prima - Transação 026',
    186.11,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '8ef08ce2-f203-4d14-893c-f53fd644e8ad',
    'REF-20251018-7935',
    'Venda de produtos - Delivery - Transação 027',
    168.17,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'b2885456-15d1-403a-88f7-7dfd39346531',
    'REF-20251018-6754',
    'Venda de produtos - Feira - Transação 028',
    83.37,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '4d3085fe-17ed-46ac-b6a0-7515864fef92',
    'REF-20251018-1801',
    'Serviços de entrega - Transação 029',
    72.24,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'dd7203e5-98e0-47a1-b517-7dfe514d2459',
    'REF-20251018-2727',
    'Taxas e impostos - Transação 030',
    112.02,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '98f4b06a-99dc-4cfc-8b12-c5642284f04e',
    'REF-20251018-4773',
    'Serviços de limpeza - Transação 031',
    123.85,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'c535a47b-b590-4612-b745-b9e10d8edbe6',
    'REF-20251018-3593',
    'Conta de energia elétrica - Transação 032',
    85.86,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '488edbce-3f93-4a11-bf38-8c3faf6a870b',
    'REF-20251018-2639',
    'Marketing e publicidade - Transação 033',
    257.92,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'd57a4a87-4453-4389-a97b-2b0fe6862ea4',
    'REF-20251018-3044',
    'Marketing e publicidade - Transação 034',
    54.32,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'af03efd9-c587-4d9f-9c54-715a3867588e',
    'REF-20251018-4102',
    'Conta de energia elétrica - Transação 035',
    182.48,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '38730124-8e39-4079-b8d8-6d47c5876b46',
    'REF-20251018-4451',
    'Aluguel do estabelecimento - Transação 036',
    615.84,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '88afa365-f01f-4e45-a8f6-0ecb3cea452d',
    'REF-20251018-4726',
    'Venda de produtos - Atacado - Transação 037',
    372.04,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'c28e128c-285f-48bb-b77e-cd6f6ba9141a',
    'REF-20251018-6866',
    'Conta de água - Transação 038',
    95.05,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '992371b6-691c-484a-bc35-de0cb5860b1a',
    'REF-20251018-6040',
    'Combustível para veículos - Transação 039',
    62.33,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'aea73fd0-936b-40d1-a3af-8f197fa538df',
    'REF-20251018-5408',
    'Seguro do negócio - Transação 040',
    211.67,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'cddf8c7a-6615-48cf-be14-64ed32ea2eef',
    'REF-20251018-6902',
    'Marketing corporativo - Contrato 01',
    3511.46,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '3668bcea-a68b-4a5d-af4f-c43d65870f7e',
    'REF-20251018-6564',
    'Serviços de consultoria empresarial - Contrato 02',
    12754.03,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '63c0b8d5-d265-4638-b500-fc3512ff1b2a',
    'REF-20251018-2679',
    'Aluguel da sede corporativa - Contrato 03',
    3716.7,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '90b955b9-409a-4c12-a61a-6c46f665160b',
    'REF-20251018-7131',
    'Marketing corporativo - Contrato 04',
    1789.17,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '94bdd166-ccd0-49dd-bb46-59ad7cd47aaa',
    'REF-20251018-1161',
    'Serviços de consultoria empresarial - Contrato 05',
    4790.23,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '5c18a2bf-8e0b-4ace-89ac-ba75f1b776cb',
    'REF-20251018-3411',
    'Vendas corporativas - Q3 2025 - Contrato 06',
    23091.38,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'e8ea842f-3455-4246-9434-156a269ced55',
    'REF-20251018-7121',
    'Serviços de consultoria empresarial - Contrato 07',
    13558.34,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'acb8a5f1-4c64-4b74-8fe8-7a94ae4e5ad3',
    'REF-20251018-9093',
    'Serviços de consultoria empresarial - Contrato 08',
    12747.27,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    'c66d05d9-0f2a-4887-963c-bce102f7a480',
    'REF-20251018-8030',
    'Marketing corporativo - Contrato 09',
    2146.76,
    '2025-10-17 18:27:00',
    'despesa',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);

INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '46ba201c-32f7-453a-9e37-539190948a79',
    'REF-20251018-6124',
    'Vendas B2B - Contrato anual - Contrato 10',
    31948.92,
    '2025-10-17 18:27:00',
    'receita',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51',
    '2025-10-18 16:44:51'
);


-- Verificar os registros inseridos:
SELECT 
    COUNT(*) as total_registros,
    COUNT(CASE WHEN transaction_type = 'receita' THEN 1 END) as receitas,
    COUNT(CASE WHEN transaction_type = 'despesa' THEN 1 END) as despesas,
    SUM(amount) as valor_total
FROM financial_transactions 
WHERE DATE(transaction_date) = '2025-10-17';

-- Listar algumas transações:
SELECT 
    reference,
    description,
    amount,
    transaction_type,
    transaction_date
FROM financial_transactions 
WHERE DATE(transaction_date) = '2025-10-17'
ORDER BY amount DESC
LIMIT 10;
