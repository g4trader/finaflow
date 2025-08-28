# 📊 Guia de Importação CSV - FinaFlow

## 🎯 Visão Geral

O sistema FinaFlow agora possui funcionalidade completa para importação de dados CSV diretamente para o BigQuery. Esta funcionalidade permite carregar:

- **Contas** com saldos iniciais
- **Transações** financeiras
- **Plano de Contas** completo (grupos, subgrupos e contas)

## 🚀 Como Usar

### 1. **Acesso à Interface Web**

Acesse a página de importação CSV:
```
http://localhost:3000/csv-import
```

### 2. **Tipos de Importação Disponíveis**

#### 📋 **Contas** (`/csv/import/accounts`)
- Importa contas com saldo inicial
- Requer: Nome da conta, Subgrupo, Saldo
- Opcional: Descrição

#### 💰 **Transações** (`/csv/import/transactions`)
- Importa movimentações financeiras
- Requer: Data, Conta, Valor, Descrição
- Suporta valores negativos (despesas)

#### 🏗️ **Plano de Contas** (`/csv/import/plan-accounts`)
- Importa estrutura completa do plano de contas
- Cria automaticamente grupos e subgrupos
- Requer: Conta, Subgrupo, Grupo, Escolha

## 📁 Estrutura dos Arquivos CSV

### **Template para Contas**
```csv
Conta,Subgrupo,Saldo,Descrição
Conta Corrente,Bancos,1000.00,Conta principal da empresa
Caixa,Caixa,500.00,Caixa da empresa
Poupança,Bancos,2000.00,Conta poupança
```

### **Template para Transações**
```csv
Data Movimentação,Conta,Valor,Descrição
02/01/2025,Conta Corrente,100.00,Recebimento de cliente
03/01/2025,Caixa,-50.00,Compra de material
04/01/2025,Conta Corrente,250.00,Venda de produto
```

### **Template para Plano de Contas**
```csv
Conta,Subgrupo,Grupo,Escolha
Conta Corrente,Bancos,Ativo,Usar
Caixa,Caixa,Ativo,Usar
Vendas,Receitas,Receita,Usar
Fornecedores,Passivo,Passivo,Usar
```

## 🔧 Endpoints da API

### **Importação**
- `POST /csv/import-csv` - Importação genérica (especificar tabela)
- `POST /csv/import/accounts` - Importar contas
- `POST /csv/import/transactions` - Importar transações
- `POST /csv/import/plan-accounts` - Importar plano de contas

### **Templates**
- `GET /csv/template/accounts` - Baixar template de contas
- `GET /csv/template/transactions` - Baixar template de transações
- `GET /csv/template/plan-accounts` - Baixar template do plano de contas

## 📋 Exemplo de Uso via API

### **1. Login para obter token**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### **2. Importar contas**
```bash
curl -X POST "http://localhost:8000/csv/import/accounts" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -F "file=@contas.csv"
```

### **3. Importar transações**
```bash
curl -X POST "http://localhost:8000/csv/import/transactions" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -F "file=@transacoes.csv"
```

### **4. Importar plano de contas**
```bash
curl -X POST "http://localhost:8000/csv/import/plan-accounts" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -F "file=@plano_contas.csv"
```

## 📊 Processamento dos Dados

### **Validações Automáticas**
- ✅ Verificação de formato CSV
- ✅ Validação de campos obrigatórios
- ✅ Conversão de valores monetários
- ✅ Parsing de datas (DD/MM/AAAA, YYYY-MM-DD)
- ✅ Verificação de tenant_id
- ✅ Tratamento de erros por linha

### **Conversões Realizadas**
- **Valores monetários**: Remove espaços, R$, pontos e converte vírgula para ponto
- **Datas**: Converte para formato ISO
- **IDs**: Gera UUIDs únicos automaticamente
- **Timestamps**: Adiciona created_at automaticamente

## 🛠️ Exemplo Prático

### **Passo 1: Preparar arquivo CSV**
Crie um arquivo `minhas_contas.csv`:
```csv
Conta,Subgrupo,Saldo,Descrição
Banco do Brasil,Bancos,5000.00,Conta principal
Caixa da Empresa,Caixa,1000.00,Caixa operacional
Nubank,Bancos,2000.00,Conta digital
```

### **Passo 2: Fazer upload via interface web**
1. Acesse `http://localhost:3000/csv-import`
2. Selecione "Contas" no tipo de importação
3. Clique em "Baixar Template CSV" para verificar o formato
4. Selecione seu arquivo `minhas_contas.csv`
5. Clique em "Importar Dados"

### **Passo 3: Verificar resultado**
```json
{
  "message": "Contas importadas com sucesso",
  "imported_count": 3,
  "tenant_id": "seu_tenant_id"
}
```

## ⚠️ Considerações Importantes

### **Formato de Dados**
- Use **vírgula** como separador decimal para valores monetários
- Use **DD/MM/AAAA** para datas
- Certifique-se de que o arquivo está em **UTF-8**
- Não use aspas desnecessárias nos campos

### **Limitações**
- Arquivos muito grandes podem demorar para processar
- Todos os registros devem pertencer ao mesmo tenant
- Valores monetários devem ser números válidos
- Datas devem estar em formato reconhecível

### **Tratamento de Erros**
- Linhas com erro são reportadas individualmente
- A importação continua mesmo com alguns erros
- Relatório detalhado de sucessos e falhas

## 🔍 Debugging

### **Logs do Servidor**
Verifique os logs do backend para detalhes de processamento:
```bash
cd backend
uvicorn app.main:app --reload --log-level debug
```

### **Teste via Script**
Execute o script de teste para verificar a funcionalidade:
```bash
python3 test_csv_import.py
```

## 📈 Próximas Melhorias

- [ ] Suporte a arquivos Excel (.xlsx)
- [ ] Validação em tempo real
- [ ] Preview dos dados antes da importação
- [ ] Mapeamento customizado de colunas
- [ ] Importação em lote de múltiplos arquivos
- [ ] Rollback de importações com erro
- [ ] Relatórios de importação detalhados

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verifique os logs do servidor
2. Teste com arquivos menores
3. Valide o formato do CSV
4. Consulte a documentação da API
5. Execute os testes automatizados

---

**Versão**: 1.0  
**Data**: $(date)  
**Status**: ✅ Funcional
