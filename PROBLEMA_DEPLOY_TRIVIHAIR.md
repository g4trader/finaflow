# ❌ Problema no Deploy do Cloud Run - Projeto Trivihair

## 🔍 Diagnóstico

O deploy falhou com o seguinte erro:

```
connection to server at "34.70.102.98", port 5432 failed: Connection timed out
```

### Status Atual

- ✅ **Migração de Código**: Concluída
  - Todos os arquivos atualizados para o projeto `trivihair`
  - Credenciais do GCP configuradas
  - Imagem Docker construída e enviada para GCR com sucesso

- ❌ **Deploy no Cloud Run**: Falhou
  - Container não consegue iniciar
  - Não consegue conectar ao banco de dados PostgreSQL em `34.70.102.98:5432`
  - Erro: **Connection timed out**

## 🎯 Causa do Problema

O Cloud Run **não consegue acessar** o banco de dados PostgreSQL no IP `34.70.102.98` porque:

1. **Firewall**: O banco de dados pode não permitir conexões dos IPs do Cloud Run
2. **Rede Privada**: O banco pode estar em uma rede privada (VPC) não acessível publicamente
3. **VPC Connector**: Cloud Run precisa de um VPC Connector para acessar recursos em redes privadas

## ✅ Soluções Possíveis

### Opção 1: Configurar VPC Connector (Recomendado se o banco estiver no GCP)

Se o banco PostgreSQL estiver em uma VM do GCP ou Cloud SQL em rede privada:

```bash
# 1. Criar VPC Connector
gcloud compute networks vpc-access connectors create finaflow-connector \
  --region=us-central1 \
  --range=10.8.0.0/28

# 2. Deploy com VPC Connector
gcloud run deploy finaflow-backend \
  --image gcr.io/trivihair/finaflow-backend:latest \
  --region us-central1 \
  --vpc-connector finaflow-connector \
  --set-env-vars "DATABASE_URL=postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db" \
  --allow-unauthenticated
```

**Custo**: ~$8-15/mês pelo VPC Connector

### Opção 2: Usar Cloud SQL (Recomendado para Produção)

Migrar para Cloud SQL PostgreSQL gerenciado pelo Google:

```bash
# 1. Criar instância Cloud SQL
gcloud sql instances create finaflow-postgres \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=senha_forte_aqui

# 2. Criar banco de dados
gcloud sql databases create finaflow_db --instance=finaflow-postgres

# 3. Criar usuário
gcloud sql users create finaflow_user \
  --instance=finaflow-postgres \
  --password=senha_forte_aqui

# 4. Obter connection name
gcloud sql instances describe finaflow-postgres --format="value(connectionName)"
# Retorna algo como: trivihair:us-central1:finaflow-postgres

# 5. Deploy usando Cloud SQL
gcloud run deploy finaflow-backend \
  --image gcr.io/trivihair/finaflow-backend:latest \
  --region us-central1 \
  --add-cloudsql-instances trivihair:us-central1:finaflow-postgres \
  --set-env-vars "DATABASE_URL=postgresql://finaflow_user:senha_forte_aqui@/finaflow_db?host=/cloudsql/trivihair:us-central1:finaflow-postgres" \
  --allow-unauthenticated
```

**Custo**: ~$10-20/mês para db-f1-micro

**Vantagens**:
- ✅ Backup automático
- ✅ Alta disponibilidade
- ✅ Segurança melhorada
- ✅ Conexão direta do Cloud Run (sem VPC Connector)

### Opção 3: Liberar Firewall do Banco Existente

Se o banco em `34.70.102.98` puder aceitar conexões públicas:

```bash
# 1. Descobrir os IPs do Cloud Run (não fixos)
# Cloud Run usa IPs dinâmicos, então precisa liberar um range ou usar Cloud NAT

# 2. Configurar Cloud NAT para IP fixo
gcloud compute addresses create finaflow-nat-ip --region=us-central1

# 3. Criar Cloud Router
gcloud compute routers create finaflow-router \
  --network=default \
  --region=us-central1

# 4. Criar Cloud NAT
gcloud compute routers nats create finaflow-nat \
  --router=finaflow-router \
  --region=us-central1 \
  --nat-external-ip-pool=finaflow-nat-ip \
  --nat-all-subnet-ip-ranges

# 5. Obter o IP fixo
gcloud compute addresses describe finaflow-nat-ip --region=us-central1 --format="value(address)"

# 6. Liberar este IP no firewall do banco de dados 34.70.102.98

# 7. Deploy com VPC e Cloud NAT
gcloud compute networks vpc-access connectors create finaflow-connector \
  --region=us-central1 \
  --range=10.8.0.0/28

gcloud run deploy finaflow-backend \
  --image gcr.io/trivihair/finaflow-backend:latest \
  --region us-central1 \
  --vpc-connector finaflow-connector \
  --vpc-egress=all-traffic \
  --set-env-vars "DATABASE_URL=postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db" \
  --allow-unauthenticated
```

**Custo**: ~$45-60/mês (NAT + VPC Connector)

### Opção 4: Deploy Temporário com SQLite (Para Testar)

Para verificar se o resto do deploy funciona, podemos temporariamente usar SQLite:

```bash
# Modificar cloudbuild.yaml para usar SQLite temporariamente
# Apenas para teste - NÃO usar em produção

gcloud run deploy finaflow-backend \
  --image gcr.io/trivihair/finaflow-backend:latest \
  --region us-central1 \
  --set-env-vars "DATABASE_URL=sqlite:///./finaflow.db" \
  --allow-unauthenticated
```

**⚠️ ATENÇÃO**: SQLite no Cloud Run perde dados entre reinicializações! Use apenas para teste.

## 📋 Recomendação

**Para Produção**: Use **Opção 2 (Cloud SQL)**
- Mais seguro
- Mais confiável
- Mais fácil de gerenciar
- Backup automático

**Para Desenvolvimento**: Use **Opção 1 (VPC Connector)**
- Mais barato
- Mantém banco existente

## 🚀 Próximos Passos

1. **Escolher uma opção** acima baseada nas suas necessidades
2. **Executar os comandos** da opção escolhida
3. **Testar o deploy**: O container deve iniciar corretamente
4. **Atualizar frontend** no Vercel com a URL do Cloud Run
5. **Criar usuário admin** no novo banco (se usar Cloud SQL)

## 📞 Informações de Suporte

### Verificar Status do Banco

```bash
# Testar conexão ao banco de 34.70.102.98
telnet 34.70.102.98 5432

# OU
nc -zv 34.70.102.98 5432

# OU com psql
psql -h 34.70.102.98 -U finaflow_user -d finaflow_db
```

### Logs do Cloud Run

```bash
# Ver logs em tempo real
gcloud run services logs tail finaflow-backend --region us-central1

# Ver logs das últimas tentativas
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=finaflow-backend" --limit 50 --project=trivihair
```

### Deletar Serviço (se necessário)

```bash
# Deletar serviço do Cloud Run para limpar
gcloud run services delete finaflow-backend --region us-central1
```

## 📊 Resumo dos Custos

| Opção | Custo Mensal Estimado | Complexidade |
|-------|----------------------|--------------|
| VPC Connector | ~$8-15 | Média |
| Cloud SQL + Connector | ~$18-35 | Baixa |
| Cloud SQL (sem connector) | ~$10-20 | Baixa ✅ |
| NAT + VPC | ~$45-60 | Alta |
| SQLite (teste) | $0 | Baixa (não recomendado) |

---

**Atualizado**: 15 de Outubro de 2025  
**Status**: Aguardando decisão sobre solução de banco de dados


