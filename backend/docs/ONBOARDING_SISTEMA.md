# Sistema de Onboarding de Empresas

## Visão Geral

O sistema de onboarding foi criado para permitir a ativação de novas empresas no FinaFlow de forma visual e estruturada, com importação de dados financeiros diretamente de planilhas Excel ou Google Sheets.

## Funcionalidades

### 1. Interface Visual de Onboarding

- **Localização:** `/admin/onboarding`
- **Acesso:** Apenas super administradores
- **Fluxo:**
  1. **URL da Planilha:** Usuário insere URL da planilha (Google Sheets ou Excel hospedado)
  2. **Validação:** Sistema valida se a planilha contém as abas necessárias
  3. **Importação:** Processo em etapas com progress tracking
  4. **Conciliação:** Tela final mostrando diferenças entre planilha e sistema

### 2. Integração na Listagem de Empresas

- **Localização:** `/admin/companies`
- **Ícone de Onboarding:** Cada Business Unit tem um botão "Onboarding" que abre a tela de onboarding
- **Dados pré-preenchidos:** Tenant ID e Business Unit ID são passados automaticamente

### 3. Endpoints de API

#### `POST /api/v1/onboarding/validate-spreadsheet`
Valida se a URL da planilha é acessível e contém as abas necessárias.

**Request:**
```json
{
  "url": "https://docs.google.com/spreadsheets/d/...",
  "tenant_id": "uuid",
  "business_unit_id": "uuid"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Planilha válida",
  "available_sheets": ["Plano de contas", "Lançamento Diário", ...],
  "found_sheets": {
    "Plano de contas": "Plano de contas",
    "Lançamento Diário": "Lançamento Diario"
  }
}
```

#### `POST /api/v1/onboarding/import`
Inicia processo de importação de dados em etapas (background task).

**Request:**
```json
{
  "tenant_id": "uuid",
  "business_unit_id": "uuid",
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
  "reset_data": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Importação iniciada",
  "status_key": "tenant_id_business_unit_id"
}
```

#### `GET /api/v1/onboarding/status/{tenant_id}/{business_unit_id}`
Retorna status atual do onboarding.

**Response:**
```json
{
  "tenant_id": "uuid",
  "business_unit_id": "uuid",
  "status": "importing_transactions",
  "current_step": "Importando Lançamentos Financeiros",
  "progress": 60,
  "message": "Importando lançamentos diários e previstos...",
  "errors": [],
  "stats": {
    "contas_importadas": 96,
    "grupos_importados": 7,
    "subgrupos_importados": 13
  }
}
```

**Status possíveis:**
- `not_started`: Onboarding não iniciado
- `validating`: Validando planilha
- `importing_plan`: Importando plano de contas
- `importing_transactions`: Importando lançamentos financeiros
- `reconciling`: Gerando conciliação
- `completed`: Concluído com sucesso
- `error`: Erro durante o processo

#### `GET /api/v1/onboarding/reconciliation/{tenant_id}/{business_unit_id}`
Retorna relatório de conciliação entre planilha e sistema.

**Response:**
```json
{
  "tenant_id": "uuid",
  "business_unit_id": "uuid",
  "reconciliation_date": "2026-01-03T...",
  "status": "completed",
  "all_reconciled": true,
  "totals": {
    "revenue": {
      "excel": 1092261.12,
      "system": 1102490.83,
      "diff": -10229.71
    },
    "expense": {
      "excel": 488812.69,
      "system": 491183.31,
      "diff": -2370.62
    },
    "cost": {
      "excel": 396229.67,
      "system": 347107.64,
      "diff": 49122.03
    },
    "balance": {
      "excel": 207218.76,
      "system": 264199.88,
      "diff": -56981.12
    }
  },
  "monthly": [
    {
      "month": 1,
      "revenue": {
        "excel": 86026.29,
        "system": 86153.06,
        "diff": -126.77
      },
      ...
    },
    ...
  ]
}
```

## Processo de Importação

### Etapas

1. **Validação da Planilha**
   - Baixa planilha da URL fornecida
   - Verifica se contém abas necessárias:
     - "Plano de contas" (ou variações)
     - "Lançamento Diário" (ou variações)
     - "Lançamentos Previstos" (ou variações)

2. **Importação do Plano de Contas**
   - Importa grupos, subgrupos e contas
   - Cria estrutura hierárquica completa
   - Progress: 30-50%

3. **Importação de Lançamentos**
   - Importa lançamentos diários (realizados)
   - Importa lançamentos previstos
   - Progress: 60-90%

4. **Conciliação**
   - Compara totais da planilha com sistema
   - Gera relatório de diferenças
   - Progress: 95-100%

## Suporte a Google Sheets

O sistema suporta URLs do Google Sheets. A conversão automática é feita:

- URL de edição: `.../edit#gid=...` → `.../export?format=xlsx`
- URL de visualização: `.../view#gid=...` → `.../export?format=xlsx`
- URL sem sufixo: `.../d/ID` → `.../d/ID/export?format=xlsx`

**Importante:** A planilha deve estar compartilhada publicamente ou o sistema deve ter acesso via credenciais.

## Tela de Conciliação

A tela de conciliação (`/admin/reconciliation`) mostra:

- **Totais Anuais:** Comparação de Receita, Despesa, Custo e Saldo
- **Totais Mensais:** Comparação mês a mês
- **Indicadores Visuais:**
  - ✅ Verde: Valores conciliados (diferença < R$ 0,01)
  - ⚠️ Laranja: Diferenças encontradas
  - ❌ Vermelho: Diferenças significativas

## Garantias de Qualidade

- **Tolerância ZERO:** Dados financeiros devem bater exatamente (diferença < R$ 0,01)
- **Idempotência:** Pode ser executado múltiplas vezes sem duplicar dados
- **Validações:** Verifica integridade hierárquica (grupo → subgrupo → conta)
- **Logs Detalhados:** Mostra progresso e estatísticas em tempo real
- **Transações:** Usa commit/rollback para garantir atomicidade

## Próximos Passos

1. ✅ Sistema de onboarding criado
2. ✅ Interface visual implementada
3. ✅ Integração na listagem de empresas
4. ✅ Tela de conciliação
5. ⚠️ Garantir 100% de conciliação (trabalho em progresso)

## Como Usar

1. Acesse `/admin/companies`
2. Clique no botão "Onboarding" ao lado de uma Business Unit
3. Cole a URL da planilha (Google Sheets ou Excel)
4. Clique em "Validar Planilha"
5. Após validação, clique em "Carregar Dados"
6. Acompanhe o progresso em tempo real
7. Ao final, visualize a conciliação

## Troubleshooting

### Planilha não encontrada
- Verifique se a URL está correta
- Para Google Sheets, certifique-se de que está compartilhada publicamente

### Erro durante importação
- Verifique os logs do backend
- Confirme que a planilha tem as abas necessárias
- Verifique se há dados válidos nas abas

### Diferenças na conciliação
- Verifique se todos os lançamentos foram importados
- Confirme que a classificação (Receita/Despesa/Custo) está correta
- Verifique se há lançamentos duplicados ou faltantes

