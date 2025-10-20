# FinaFlow API Documentation

## Autenticação

### Login
POST /auth/login
```json
{
  "username": "string",
  "password": "string"
}
```

### Registro
POST /auth/signup
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "tenant_user",
  "tenant_id": "string"
}
```

## Transações

### Listar Transações
GET /transactions/

### Criar Transação
POST /transactions/
```json
{
  "account_id": "string",
  "amount": "decimal",
  "description": "string",
  "tenant_id": "string"
}
```

### Atualizar Transação
PUT /transactions/{transaction_id}

### Deletar Transação
DELETE /transactions/{transaction_id}

## Contas

### Listar Contas
GET /accounts/

### Criar Conta
POST /accounts/
```json
{
  "subgroup_id": "string",
  "name": "string",
  "balance": "decimal",
  "tenant_id": "string"
}
```

## Relatórios

### Fluxo de Caixa
GET /reports/cash-flow?group_by=month

## Grupos e Subgrupos

### Grupos
- GET /groups/
- POST /groups/
- PUT /groups/{group_id}
- DELETE /groups/{group_id}

### Subgrupos
- GET /subgroups/
- POST /subgroups/
- PUT /subgroups/{subgroup_id}
- DELETE /subgroups/{subgroup_id}

## Previsões

### Listar Previsões
GET /forecast/

### Criar Previsão
POST /forecast/
```json
{
  "account_id": "string",
  "amount": "decimal",
  "description": "string",
  "tenant_id": "string"
}
```

## Importação CSV

### Importação Genérica
POST /csv/import-csv
```
Content-Type: multipart/form-data
file: arquivo.csv
table: nome_da_tabela
```

### Importar Contas
POST /csv/import/accounts
```
Content-Type: multipart/form-data
file: arquivo.csv
```

### Importar Transações
POST /csv/import/transactions
```
Content-Type: multipart/form-data
file: arquivo.csv
```

### Importar Plano de Contas
POST /csv/import/plan-accounts
```
Content-Type: multipart/form-data
file: arquivo.csv
```

### Baixar Template de Contas
GET /csv/template/accounts

### Baixar Template de Transações
GET /csv/template/transactions

### Baixar Template de Plano de Contas
GET /csv/template/plan-accounts

## Códigos de Status

- 200: Sucesso
- 201: Criado
- 400: Erro de validação
- 401: Não autorizado
- 403: Acesso negado
- 404: Não encontrado
- 500: Erro interno do servidor
