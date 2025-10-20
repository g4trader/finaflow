#!/usr/bin/env python3
"""
Script para gerar arquivo SQL com 50 registros sintéticos
Data: 17/10/2025
40 pequenos negócios + 10 sociedades
"""

import random
from datetime import datetime
import uuid

# Dados sintéticos para pequenos negócios (40 registros)
PEQUENOS_NEGOCIOS = [
    {"desc": "Venda de produtos - Loja", "tipo": "receita", "valor_min": 50, "valor_max": 500},
    {"desc": "Serviços de consultoria", "tipo": "receita", "valor_min": 100, "valor_max": 800},
    {"desc": "Venda de produtos online", "tipo": "receita", "valor_min": 30, "valor_max": 300},
    {"desc": "Serviços de manutenção", "tipo": "receita", "valor_min": 80, "valor_max": 400},
    {"desc": "Aluguel de equipamentos", "tipo": "receita", "valor_min": 60, "valor_max": 250},
    {"desc": "Compra de matéria-prima", "tipo": "despesa", "valor_min": 100, "valor_max": 600},
    {"desc": "Pagamento de funcionários", "tipo": "despesa", "valor_min": 200, "valor_max": 1200},
    {"desc": "Aluguel do estabelecimento", "tipo": "despesa", "valor_min": 300, "valor_max": 800},
    {"desc": "Conta de energia elétrica", "tipo": "despesa", "valor_min": 80, "valor_max": 200},
    {"desc": "Conta de água", "tipo": "despesa", "valor_min": 40, "valor_max": 120},
    {"desc": "Combustível para veículos", "tipo": "despesa", "valor_min": 60, "valor_max": 180},
    {"desc": "Marketing e publicidade", "tipo": "despesa", "valor_min": 50, "valor_max": 300},
    {"desc": "Material de escritório", "tipo": "despesa", "valor_min": 30, "valor_max": 150},
    {"desc": "Seguro do negócio", "tipo": "despesa", "valor_min": 80, "valor_max": 250},
    {"desc": "Taxas e impostos", "tipo": "despesa", "valor_min": 100, "valor_max": 400},
    {"desc": "Venda de produtos - Feira", "tipo": "receita", "valor_min": 40, "valor_max": 350},
    {"desc": "Serviços de entrega", "tipo": "receita", "valor_min": 25, "valor_max": 150},
    {"desc": "Venda de produtos - Delivery", "tipo": "receita", "valor_min": 35, "valor_max": 200},
    {"desc": "Serviços de limpeza", "tipo": "receita", "valor_min": 50, "valor_max": 180},
    {"desc": "Venda de produtos - Atacado", "tipo": "receita", "valor_min": 200, "valor_max": 800},
]

# Dados sintéticos para sociedades (10 registros)
SOCIEDADES = [
    {"desc": "Vendas corporativas - Q3 2025", "tipo": "receita", "valor_min": 5000, "valor_max": 25000},
    {"desc": "Serviços de consultoria empresarial", "tipo": "receita", "valor_min": 3000, "valor_max": 15000},
    {"desc": "Licenciamento de software", "tipo": "receita", "valor_min": 2000, "valor_max": 8000},
    {"desc": "Folha de pagamento - Outubro", "tipo": "despesa", "valor_min": 8000, "valor_max": 30000},
    {"desc": "Aluguel da sede corporativa", "tipo": "despesa", "valor_min": 2000, "valor_max": 6000},
    {"desc": "Investimento em tecnologia", "tipo": "despesa", "valor_min": 1500, "valor_max": 5000},
    {"desc": "Marketing corporativo", "tipo": "despesa", "valor_min": 1000, "valor_max": 4000},
    {"desc": "Consultoria jurídica", "tipo": "despesa", "valor_min": 800, "valor_max": 3000},
    {"desc": "Vendas B2B - Contrato anual", "tipo": "receita", "valor_min": 10000, "valor_max": 40000},
    {"desc": "Prestação de serviços especializados", "tipo": "receita", "valor_min": 4000, "valor_max": 18000},
]

def gerar_valor(min_val, max_val):
    """Gera um valor aleatório entre min e max"""
    return round(random.uniform(min_val, max_val), 2)

def gerar_uuid():
    """Gera um UUID único"""
    return str(uuid.uuid4())

def main():
    """Função principal"""
    print("="*80)
    print("  🎯 GERADOR DE SCRIPT SQL - DADOS SINTÉTICOS")
    print("="*80)
    print(f"📅 Data: 17/10/2025")
    print(f"📊 Registros: 40 pequenos negócios + 10 sociedades")
    print("="*80 + "\n")
    
    # Data da transação
    data_transacao = datetime(2025, 10, 17, random.randint(8, 18), random.randint(0, 59))
    data_str = data_transacao.strftime('%Y-%m-%d %H:%M:%S')
    created_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    # Iniciar o script SQL
    sql_content = f"""-- Script SQL para inserir 50 registros sintéticos
-- Data: 17/10/2025
-- 40 pequenos negócios + 10 sociedades
-- Gerado em: {created_at}

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

"""
    
    print("📝 Gerando script SQL...")
    
    # Gerar 40 registros de pequenos negócios
    print("🏪 Gerando pequenos negócios...")
    for i in range(40):
        item = random.choice(PEQUENOS_NEGOCIOS)
        valor = gerar_valor(item["valor_min"], item["valor_max"])
        
        # Adicionar variação na descrição
        descricao = f"{item['desc']} - Transação {i+1:03d}"
        reference = f"REF-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        transaction_id = gerar_uuid()
        
        sql_content += f"""INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '{transaction_id}',
    '{reference}',
    '{descricao}',
    {valor},
    '{data_str}',
    '{item["tipo"]}',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '{created_at}',
    '{created_at}',
    '{created_at}'
);

"""
    
    # Gerar 10 registros de sociedades
    print("🏢 Gerando sociedades...")
    for i in range(10):
        item = random.choice(SOCIEDADES)
        valor = gerar_valor(item["valor_min"], item["valor_max"])
        
        # Adicionar variação na descrição
        descricao = f"{item['desc']} - Contrato {i+1:02d}"
        reference = f"REF-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        transaction_id = gerar_uuid()
        
        sql_content += f"""INSERT INTO financial_transactions (
    id, reference, description, amount, transaction_date, transaction_type, status,
    chart_account_id, tenant_id, business_unit_id, created_by, approved_by,
    is_active, created_at, updated_at, approved_at
) VALUES (
    '{transaction_id}',
    '{reference}',
    '{descricao}',
    {valor},
    '{data_str}',
    '{item["tipo"]}',
    'aprovada',
    (SELECT id FROM chart_accounts LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM tenants LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM business_units LIMIT 1), -- Substitua pelo ID real
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
    true,
    '{created_at}',
    '{created_at}',
    '{created_at}'
);

"""
    
    # Finalizar o script
    sql_content += f"""
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
"""
    
    # Salvar o arquivo SQL
    filename = f"synthetic_data_2025_10_17.sql"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print(f"\n" + "="*80)
    print(f"  🎉 SCRIPT SQL GERADO COM SUCESSO!")
    print("="*80)
    print(f"📄 Arquivo: {filename}")
    print(f"📊 Total de registros: 50")
    print(f"🏪 Pequenos negócios: 40")
    print(f"🏢 Sociedades: 10")
    print(f"📅 Data: 17/10/2025")
    print(f"\n💡 Instruções:")
    print(f"   1. Abra o arquivo {filename}")
    print(f"   2. Substitua os IDs pelos valores reais do seu banco")
    print(f"   3. Execute o script no seu banco PostgreSQL")
    print(f"   4. Ou aguarde o backend voltar ao normal e use a API")
    print("="*80)

if __name__ == "__main__":
    main()
