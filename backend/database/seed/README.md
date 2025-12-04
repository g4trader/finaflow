# 📊 Seed do Ambiente STAGING

Script completo e idempotente para popular o banco de dados de STAGING com dados reais da planilha do cliente.

## 📋 Estrutura

```
backend/database/seed/
├── seed_staging.py    # Script principal de seed
└── README.md          # Este arquivo
```

## 🎯 Objetivo

Popular o ambiente STAGING com:
1. **Plano de Contas completo**: Grupos, Subgrupos e Contas
2. **Lançamentos Financeiros (Diários)**: Histórico de transações realizadas
3. **Lançamentos Previstos**: Previsões futuras de transações

## 📁 Planilha Google Sheets

O script lê dados diretamente da planilha Google Sheets:

**URL**: https://docs.google.com/spreadsheets/d/1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ

**Abas necessárias:**
- `Plano de contas|LLM` (ou `Plano de contas`)
- `Lançamento Diário` (ou `Lançamento Diario`)
- `Lançamentos Previstos` (ou `Lancamentos Previstos`)

## 🔧 Pré-requisitos

1. **Python 3.8+**
2. **Dependências instaladas**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Arquivo de credenciais Google**:
   - `google_credentials.json` na raiz do backend
   - Ou configure `GOOGLE_APPLICATION_CREDENTIALS` com o caminho do arquivo
   - O arquivo deve ter permissões de leitura na planilha Google Sheets

4. **Variáveis de ambiente** (opcionais):
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/db"
   export GOOGLE_APPLICATION_CREDENTIALS="/caminho/para/google_credentials.json"  # Opcional
   export STAGING_TENANT_ID="uuid-do-tenant"  # Opcional
   export STAGING_BUSINESS_UNIT_ID="uuid-da-bu"  # Opcional
   export STAGING_USER_ID="uuid-do-usuario"  # Opcional
   ```

## 🚀 Como Usar

### 1. Preparar credenciais Google

Certifique-se de que o arquivo `google_credentials.json` está na raiz do backend e tem acesso à planilha.

### 2. Executar o seed

```bash
cd backend
python database/seed/seed_staging.py
```

### 3. Verificar os logs

O script exibe logs detalhados durante a execução:
- ✅ Sucessos
- ⚠️ Avisos
- ❌ Erros
- 📊 Estatísticas finais

## 📊 Estrutura das Abas da Planilha

### Plano de Contas

**Colunas esperadas:**
- `Conta` (ou `conta`, `CONTA`): Nome da conta
- `Subgrupo` (ou `subgrupo`, `SUBGRUPO`): Nome do subgrupo
- `Grupo` (ou `grupo`, `GRUPO`): Nome do grupo
- `Escolha` (ou `escolha`, `ESCOLHA`): "Usar" para incluir, outros valores para ignorar

**Exemplo:**
```
Conta                          | Subgrupo                    | Grupo                    | LLM
Vendas Cursos pelo o comercial | Receita                    | Receita                  | Usar
Salário                        | Despesas com Pessoal       | Despesas Operacionais    | Usar
```

### Lançamentos Diários

**Colunas esperadas:**
- `Data Movimentação` (ou `data_movimentacao`, `Data Movimentacao`): Data no formato DD/MM/YYYY
- `Subgrupo` (ou `subgrupo`, `SUBGRUPO`): Nome do subgrupo
- `Grupo` (ou `grupo`, `GRUPO`): Nome do grupo
- `Valor` (ou `valor`, `VALOR`): Valor no formato brasileiro (ex: "1.234,56" ou "R$ 1.234,56")
- `Observações` (ou `observacoes`, `OBSERVACOES`): Observações opcionais

**Exemplo:**
```
Ano/Mês    | Data Movimentação | (vazio)              | Subgrupo              | Grupo                    | Valor
01/01/2025 | 02/01/2025        | Vale Alimentação-ADM  | Despesas com Pessoal  | Despesas Operacionais    | 3.200,00
```

### Lançamentos Previstos

**Colunas esperadas:**
- `Mês` (ou `mes`, `MES`, `Data Prevista`, `data_prevista`): Data no formato DD/MM/YYYY
- `Conta` (ou `conta`, `CONTA`): Nome da conta
- `Subgrupo` (ou `subgrupo`, `SUBGRUPO`): Nome do subgrupo
- `Grupo` (ou `grupo`, `GRUPO`): Nome do grupo
- `Valor` (ou `valor`, `VALOR`): Valor no formato brasileiro

**Exemplo:**
```
Ano/Mês    | Mês       | Conta | Subgrupo                  | Grupo                    | Valor
01/01/2025 | 10/01/2025| Água  | Despesas Administrativas  | Despesas Operacionais    | R$ 80,0
```

## 🔄 Idempotência

O script é **idempotente**, ou seja, pode ser executado múltiplas vezes sem duplicar dados:

- **Grupos/Subgrupos/Contas**: Verificados por nome + tenant_id
- **Lançamentos Diários**: Verificados por data + conta + valor + tenant + BU
- **Lançamentos Previstos**: Verificados por data + conta + valor + tenant + BU

## ✅ Validações

O script realiza as seguintes validações:

1. **Hierarquia**: Verifica que Conta → Subgrupo → Grupo está correta
2. **Tenant/BU**: Garante que todos os registros estão vinculados ao tenant e BU corretos
3. **Datas**: Valida formato e converte corretamente
4. **Valores**: Converte valores brasileiros (R$ 1.234,56) para Decimal
5. **Integridade**: Usa transações (commit/rollback) para garantir atomicidade

## 📝 Logs e Estatísticas

Ao final da execução, o script exibe:

```
📊 ESTATÍSTICAS DO SEED
============================================================
Grupos: X criados, Y existentes
Subgrupos: X criados, Y existentes
Contas: X criadas, Y existentes
Lançamentos Diários: X criados, Y existentes
Lançamentos Previstos: X criados, Y existentes
```

## ⚠️ Campos Ignorados

O script ignora automaticamente:

- Linhas vazias
- Linhas com "Escolha" diferente de "Usar" (no plano de contas)
- Valores zerados ou inválidos
- Datas inválidas ou vazias
- Registros duplicados (idempotência)

## 🔍 Troubleshooting

### Erro: "Arquivo de credenciais não encontrado"

**Solução**: Verifique se o arquivo `google_credentials.json` está na raiz do backend ou configure `GOOGLE_APPLICATION_CREDENTIALS`.

### Erro: "Aba não encontrada"

**Solução**: Verifique se as abas existem na planilha Google Sheets. O script tenta diferentes variações de nomes automaticamente.

### Erro: "Grupo não encontrado"

**Solução**: Certifique-se de que o plano de contas foi processado antes dos lançamentos. O script processa na ordem correta automaticamente.

### Erro: "Erro ao converter data"

**Solução**: Verifique o formato das datas no CSV. Formatos suportados:
- DD/MM/YYYY
- DD-MM-YYYY
- YYYY-MM-DD

### Erro: "Erro ao converter valor"

**Solução**: Verifique o formato dos valores. Formatos suportados:
- "1.234,56"
- "R$ 1.234,56"
- "1234.56"

## 🚨 Importante

- **NÃO execute este script em produção**
- **Este script é exclusivo para STAGING**
- **Sempre faça backup antes de executar** (mesmo sendo idempotente)
- **Verifique as variáveis de ambiente** antes de executar

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs de erro no console
2. Confira a estrutura dos CSVs
3. Valide as variáveis de ambiente
4. Entre em contato com o time de desenvolvimento

