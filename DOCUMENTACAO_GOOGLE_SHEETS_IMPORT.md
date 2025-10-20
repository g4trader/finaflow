# 📊 DOCUMENTAÇÃO COMPLETA - GOOGLE SHEETS IMPORT

**Rota**: https://finaflow.vercel.app/google-sheets-import  
**Data**: 19 de Outubro de 2025  
**Status**: ✅ FUNCIONALIDADE IMPLEMENTADA

---

## 🎯 OBJETIVO

Esta página permite importar dados financeiros diretamente de planilhas do **Google Sheets** para o sistema FinaFlow, especificamente planilhas que seguem a **metodologia Ana Paula** de gestão financeira.

---

## 📋 FUNCIONALIDADES PRINCIPAIS

### 1. 📊 **Visualização de Planilha de Exemplo**

Mostra informações sobre uma planilha de exemplo configurada:
- **ID da planilha** de exemplo
- **Descrição** da metodologia
- **Total de abas** disponíveis
- **Lista de abas** com seus nomes
- **Instruções** de uso
- **Botão para copiar** o ID da planilha

**Planilha Exemplo Configurada**:
- ID: `1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY`
- Título: "Fluxo de Caixa 2025|Cliente teste"
- Total de abas: 18

---

### 2. 🔍 **Validação de Planilha**

Permite validar a estrutura de uma planilha do Google Sheets antes de importar:

#### O que faz:
- ✅ Conecta com a planilha via Google Sheets API
- ✅ Analisa todas as abas da planilha
- ✅ Identifica o tipo de cada aba (contas, transações, relatórios)
- ✅ Verifica se as colunas obrigatórias existem
- ✅ Conta linhas e colunas de cada aba
- ✅ Lista os cabeçalhos encontrados
- ✅ Mostra erros de validação (se houver)

#### Resultado da Validação:
```json
{
  "success": true/false,
  "spreadsheet_title": "Nome da planilha",
  "sheets_found": ["Aba 1", "Aba 2", ...],
  "data_structure": {
    "total_sheets": 18,
    "supported_sheets": 15,
    "sheets_analysis": [
      {
        "name": "Plano de contas",
        "type": "accounts",
        "rows": 121,
        "columns": 5,
        "headers": ["Conta", "Subgrupo", "Grupo", "Escolha"]
      },
      {
        "name": "Lançamento Diário",
        "type": "transactions",
        "rows": 778,
        "columns": 8,
        "headers": ["Data", "Descrição", "Conta", "Valor", ...]
      }
    ]
  },
  "validation_errors": []
}
```

---

### 3. ✅ **Validação de Importação (Dry Run)**

Simula a importação sem gravar dados no banco:

#### O que faz:
- ✅ Processa todos os dados como se fosse importar
- ✅ Identifica erros potenciais
- ✅ Mostra quantos registros seriam importados
- ✅ **NÃO grava** nada no banco de dados
- ✅ Útil para testar antes da importação real

#### Resultado:
```json
{
  "success": true,
  "message": "Validação bem-sucedida",
  "data_imported": {
    "groups": 7,
    "subgroups": 25,
    "accounts": 120,
    "transactions": 778,
    "forecasts": 665
  },
  "errors": []
}
```

---

### 4. 📥 **Importação de Dados**

Importa os dados da planilha para o banco de dados:

#### O que faz:
- ✅ Lê todas as abas da planilha
- ✅ Categoriza automaticamente os dados
- ✅ Cria a estrutura hierárquica (Grupos → Subgrupos → Contas)
- ✅ Importa transações realizadas e previstas
- ✅ Importa relatórios e fluxos de caixa
- ✅ **Grava tudo no banco de dados**
- ✅ Associa à Business Unit selecionada
- ✅ Registra quem fez a importação

#### Tipos de Importação:
1. **"all"** (Todos os dados)
   - Estrutura de contas
   - Transações
   - Previsões
   - Relatórios

2. **"accounts"** (Apenas estrutura de contas)
   - Grupos
   - Subgrupos  
   - Contas
   
3. **"transactions"** (Apenas transações)
   - Lançamentos diários
   - Lançamentos previstos
   
4. **"reports"** (Apenas relatórios)
   - Fluxos de caixa mensais
   - Resultados anuais

---

## 🗂️ ABAS DA PLANILHA RECONHECIDAS

### 📊 **Estrutura de Contas**
1. **Plano de contas**
   - Colunas: Conta, Subgrupo, Grupo, Escolha
   - ~121 linhas
   - Cria a hierarquia completa de contas

### 💰 **Transações**
2. **Lançamento Diário**
   - ~778 transações realizadas
   - Colunas: Data, Descrição, Conta, Valor, etc
   
3. **Lançamentos Previstos**  
   - ~665 transações futuras
   - Mesma estrutura do Lançamento Diário

### 📈 **Relatórios e Fluxos**
4. **Fluxo de caixa-2025**
   - Consolidado anual (~179 linhas)
   
5. **Previsão Fluxo de caixa-2025**
   - Previsão anual (~179 linhas)
   
6. **FC-diário-Jan2025** até **FC-diário-Dez2025**
   - 12 abas (uma por mês)
   - ~195 linhas cada
   - Fluxo de caixa diário detalhado

7. **Resultados Anuais**
   - Resumo executivo (~2 linhas)

---

## 🔧 COMO USAR

### Passo 1: Acessar a Página
```
https://finaflow.vercel.app/google-sheets-import
```

### Passo 2: Obter ID da Planilha Google Sheets

#### Opção A: Usar a planilha de exemplo
- O ID já vem preenchido na página
- ID: `1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY`

#### Opção B: Usar sua própria planilha
1. Abra sua planilha no Google Sheets
2. Copie o ID da URL:
   ```
   https://docs.google.com/spreadsheets/d/[ID_AQUI]/edit
   ```
3. Cole o ID no campo da página

### Passo 3: Escolher Tipo de Importação
- **Todos os dados**: Importa tudo
- **Apenas estrutura de contas**: Só o plano de contas
- **Apenas transações**: Só lançamentos
- **Apenas relatórios**: Só fluxos e resumos

### Passo 4: Validar (Recomendado)
1. Clique em **"🔍 Validar Planilha"**
2. Revise as abas encontradas
3. Verifique se há erros

### Passo 5: Validar Importação (Opcional)
1. Clique em **"✅ Validar Importação"**
2. Veja quantos registros seriam importados
3. Confirme se os números fazem sentido

### Passo 6: Importar
1. Clique em **"📥 Importar Dados"**
2. Aguarde o processamento (pode demorar 30-60 segundos)
3. Verifique o resultado

---

## 📊 RESULTADO DA IMPORTAÇÃO

### ✅ Sucesso
```
✅ Importação bem-sucedida!

Dados importados:
- Grupos: 7
- Subgrupos: 25
- Contas: 120
- Transações: 778
- Previsões: 665
```

### ❌ Erro
```
❌ Erros encontrados na importação

Erros:
• Linha 45: Coluna 'Data' não encontrada
• Linha 67: Valor inválido para 'Conta'
• Aba 'Lançamentos': Cabeçalho 'Valor' não encontrado
```

---

## 🔐 REQUISITOS E PERMISSÕES

### Autenticação
- ✅ Usuário deve estar **logado** no sistema
- ✅ Ter uma **Business Unit selecionada**
- ✅ Ter **permissão** de importação (role: admin ou super_admin)

### Google Sheets
- ✅ Planilha deve estar **compartilhada** com:
  - Email do Service Account do sistema
  - Ou ser pública (link compartilhado)
- ✅ Planilha deve seguir a **estrutura esperada** (metodologia Ana Paula)

---

## 🎨 INTERFACE DA PÁGINA

### Seções da Página

#### 1. **Cabeçalho**
```
📊 Importação Google Sheets
Importe dados da metodologia Ana Paula diretamente do Google Sheets
```

#### 2. **Card "Planilha de Exemplo"**
- ID da planilha de exemplo
- Botão "Copiar" para copiar o ID
- Descrição da metodologia
- Total de abas disponíveis
- Lista visual das abas (badges azuis)
- Instruções de uso

#### 3. **Card "Importar Dados"**
- Campo de input para ID da planilha
- Dropdown para tipo de importação
- 3 botões de ação:
  - 🔍 Validar Planilha (secundário)
  - ✅ Validar Importação (secundário)  
  - 📥 Importar Dados (primário)

#### 4. **Card "Resultados"** (aparece após ação)
- Status visual (✅ ou ❌)
- Mensagem de resultado
- Detalhes dos dados processados
- Lista de erros (se houver)

#### 5. **Modal "Detalhes da Validação"**
Mostra análise completa de cada aba:
- Nome da aba
- Tipo identificado
- Quantidade de linhas e colunas
- Cabeçalhos encontrados
- Status de validação

---

## 🔌 ENDPOINTS DA API BACKEND

### 1. GET `/api/v1/import/google-sheets/sample`
**Função**: Retorna informações da planilha de exemplo

**Headers**:
```
Authorization: Bearer {token}
```

**Resposta**:
```json
{
  "spreadsheet_id": "1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY",
  "description": "Planilha de exemplo com a metodologia Ana Paula",
  "sheets": ["Plano de contas", "Lançamento Diário", ...],
  "instructions": [
    "Cole o ID da planilha no campo acima",
    "Clique em Validar para verificar a estrutura",
    ...
  ]
}
```

---

### 2. POST `/api/v1/import/google-sheets/validate`
**Função**: Valida estrutura da planilha sem importar

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body**:
```json
{
  "spreadsheet_id": "1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY"
}
```

**Resposta**: Ver seção "Validação de Planilha" acima

---

### 3. POST `/api/v1/import/google-sheets`
**Função**: Importa dados da planilha

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body**:
```json
{
  "spreadsheet_id": "1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY",
  "import_type": "all",
  "validate_only": false
}
```

**Parâmetros**:
- `spreadsheet_id` (obrigatório): ID da planilha
- `import_type` (opcional): "all", "accounts", "transactions", "reports"
- `validate_only` (opcional): true = não grava, false = grava dados

**Resposta**:
```json
{
  "success": true,
  "message": "Dados importados com sucesso!",
  "spreadsheet_id": "1yyHuP6...",
  "spreadsheet_title": "Fluxo de Caixa 2025",
  "sheets_processed": ["Plano de contas", "Lançamento Diário"],
  "data_imported": {
    "groups": 7,
    "subgroups": 25,
    "accounts": 120,
    "transactions": 778
  },
  "errors": []
}
```

---

### 4. GET `/api/v1/import/status/{import_id}`
**Função**: Consulta status de uma importação

**Headers**:
```
Authorization: Bearer {token}
```

**Resposta**:
```json
{
  "import_id": "abc123",
  "status": "completed",
  "progress": 100,
  "message": "Importação concluída com sucesso"
}
```

---

## ⚙️ CONFIGURAÇÃO TÉCNICA

### Backend
- **Service Account**: Google Cloud com acesso às APIs:
  - Google Sheets API
  - Google Drive API
  
- **Credenciais**: `google_credentials.json`
  
- **Bibliotecas**:
  - `gspread` - Interface Google Sheets
  - `google-auth` - Autenticação

### Frontend
- **Página**: `frontend/pages/google-sheets-import.tsx`
- **API Client**: `frontend/services/api.ts`
  - `getSampleSpreadsheetInfo()`
  - `validateGoogleSheetsData()`
  - `importFromGoogleSheets()`
  - `getImportStatus()`

---

## 🎯 CASOS DE USO

### Caso 1: Importar planilha de cliente novo
1. Cliente envia planilha Google Sheets
2. Compartilha com o service account
3. Admin acessa `/google-sheets-import`
4. Cola o ID da planilha
5. Valida a estrutura
6. Importa os dados
7. Cliente pode acessar o sistema com seus dados

### Caso 2: Atualizar dados existentes
1. Cliente atualiza sua planilha do Google Sheets
2. Admin reimporta os dados
3. Sistema atualiza transações e relatórios

### Caso 3: Migrar de Excel para FinaFlow
1. Cliente converte Excel para Google Sheets
2. Ajusta estrutura conforme metodologia Ana Paula
3. Importa via interface
4. Valida os dados importados

---

## ⚠️ LIMITAÇÕES E OBSERVAÇÕES

### Limitações Conhecidas
1. **Formato fixo**: Planilha deve seguir estrutura Ana Paula
2. **Colunas obrigatórias**: Algumas colunas são requeridas
3. **Permissões**: Planilha deve estar compartilhada corretamente
4. **Performance**: Planilhas muito grandes (>10.000 linhas) podem demorar

### Observações Importantes
- ✅ **Importação é aditiva**: Não remove dados existentes
- ✅ **Duplicatas**: Sistema tenta evitar duplicação por chave única
- ✅ **Rollback**: Não há rollback automático (fazer backup antes)
- ✅ **Logs**: Todas importações são registradas

---

## 🐛 TROUBLESHOOTING

### Erro: "Planilha não encontrada"
**Causa**: ID incorreto ou permissões  
**Solução**: 
1. Verificar ID copiado corretamente
2. Compartilhar planilha com service account
3. Verificar se planilha não foi deletada

### Erro: "Coluna 'X' não encontrada"
**Causa**: Estrutura da planilha diferente do esperado  
**Solução**:
1. Usar planilha de exemplo como referência
2. Verificar nomes das colunas (maiúsculas/minúsculas)
3. Adicionar colunas faltantes

### Erro: "Não autorizado"
**Causa**: Token expirado ou sem permissões  
**Solução**:
1. Fazer login novamente
2. Verificar role do usuário (precisa ser admin)
3. Selecionar Business Unit

### Importação muito lenta
**Causa**: Planilha muito grande ou conexão lenta  
**Solução**:
1. Dividir em importações menores
2. Importar apenas o necessário (usar import_type específico)
3. Aguardar pacientemente (pode levar minutos)

---

## 📚 RECURSOS ADICIONAIS

### Documentos Relacionados
- `IMPLEMENTACAO_GOOGLE_SHEETS.md` - Detalhes técnicos da implementação
- `API_DOCUMENTATION.md` - Documentação completa da API
- `RELATORIO_IMPORTACAO_PLANO_CONTAS.md` - Exemplo de importação via CSV

### Links Úteis
- [Google Sheets API Docs](https://developers.google.com/sheets/api)
- [Metodologia Ana Paula](link-se-disponivel)
- [Planilha de Exemplo](https://docs.google.com/spreadsheets/d/1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY/edit)

---

## ✅ RESUMO EXECUTIVO

### O que esta funcionalidade faz:
Permite importar dados financeiros completos (estrutura de contas, transações, previsões e relatórios) diretamente de planilhas do Google Sheets para o FinaFlow, eliminando a necessidade de digitação manual.

### Benefícios:
- ⚡ **Rápido**: Importa centenas de linhas em segundos
- 🎯 **Preciso**: Validação automática evita erros
- 🔄 **Flexível**: Importa tudo ou apenas partes específicas
- 👥 **Acessível**: Interface simples e intuitiva
- 📊 **Completo**: Importa toda a estrutura de dados

### Status Atual:
✅ **FUNCIONAL e PRONTA PARA USO** em produção!

---

**Documentado por**: Sistema FinaFlow  
**Última atualização**: 2025-10-19  
**Versão**: 1.0

