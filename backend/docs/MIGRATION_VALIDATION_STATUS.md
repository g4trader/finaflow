# Migration: Tabela de Status de Validação

## Objetivo

Criar a tabela `dashboard_validation_status` para rastrear o status da última validação do dashboard contra a planilha do cliente.

## Arquivos Criados

1. **Migration SQL**: `migrations/create_dashboard_validation_status_table.sql`
   - Cria tabela com todos os campos necessários
   - Adiciona índices para performance
   - Inclui constraints e foreign keys

2. **Script de Migration**: `backend/scripts/run_migration_validation_status.py`
   - Executa a migration SQL manualmente
   - Verifica se a tabela foi criada com sucesso
   - Pode ser executado no pipeline de deploy

3. **Modelo Python**: `backend/app/models/validation_status.py` (já existia)
   - Modelo SQLAlchemy para a tabela
   - Importado no `main.py` para criação automática via `create_tables()`

## Estrutura da Tabela

```sql
CREATE TABLE dashboard_validation_status (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    business_unit_id VARCHAR(36) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- SUCCESS, FAILED, PENDING
    year VARCHAR(4) NOT NULL,
    last_validation_at TIMESTAMP NULL,
    validation_details TEXT NULL,  -- JSON com detalhes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, business_unit_id, year)
);
```

## Como Executar a Migration

### Opção 1: Via Script Python (Recomendado)

```bash
cd backend
python scripts/run_migration_validation_status.py
```

### Opção 2: Via SQL Direto

```bash
psql -h <host> -U <user> -d <database> -f migrations/create_dashboard_validation_status_table.sql
```

### Opção 3: Automático (via create_tables)

A tabela será criada automaticamente quando o backend iniciar, pois o modelo está importado no `main.py`:

```python
from app.models.validation_status import DashboardValidationStatus
```

O `create_tables()` no `app/database.py` criará a tabela automaticamente.

## Verificação

Após executar a migration, verificar se a tabela foi criada:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'dashboard_validation_status';
```

## Integração com Script de Validação

O script `validate_dashboard_against_client_sheet.py` já está configurado para:
1. Atualizar o status após validação bem-sucedida
2. Salvar detalhes da validação em JSON
3. Registrar data/hora da última validação

## Próximos Passos

1. Executar migration em STAGING
2. Executar seed + validação
3. Verificar se o status foi salvo corretamente
4. Verificar endpoint `/api/v1/system/validation-status`
5. Verificar badge no frontend

