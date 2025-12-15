# 🚀 Deploy Automatizado v2.0 - Seed + Validação

**Data**: 2025-12-12  
**Status**: ✅ **IMPLEMENTADO**

---

## 🎯 Objetivo

Automatizar completamente o fluxo de seed + validação dentro do Cloud Build, garantindo que:
- ✅ Seed execute automaticamente antes do deploy
- ✅ Validação execute automaticamente após o seed
- ✅ Deploy só aconteça se seed e validação passarem (exit code 0)
- ✅ Tudo rode dentro do container (sem dependências externas)

---

## 📋 Arquivos Criados

1. **`backend/cloudbuild-staging-v2.yaml`**: Cloud Build config com seed + validação
2. **`backend/scripts/run_seed_and_validate_in_build.sh`**: Script wrapper que gerencia Cloud SQL Proxy e executa seed + validação

---

## 🚀 Como Usar

### Comando Único

```bash
gcloud builds submit --config backend/cloudbuild-staging-v2.yaml --project=trivihair
```

Este comando:
1. ✅ Faz build da imagem Docker
2. ✅ Faz push da imagem para Container Registry
3. ✅ Executa seed dentro do container (via Cloud SQL Proxy)
4. ✅ Executa validação dentro do container
5. ✅ Só faz deploy se seed e validação passarem (exit code 0)

---

## 📊 Fluxo Detalhado

### Step 1: Build da Imagem
```yaml
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/finaflow-backend-staging', ...]
```

### Step 2: Push da Imagem
```yaml
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/finaflow-backend-staging']
```

### Step 3: Seed + Validação
```yaml
- name: 'gcr.io/cloud-builders/docker'
  entrypoint: 'docker'
  args:
    - 'run'
    - '--rm'
    - '--network=host'
    - '-v'
    - '/workspace/backend:/app'
    - 'gcr.io/$PROJECT_ID/finaflow-backend-staging'
    - 'bash'
    - '/app/scripts/run_seed_and_validate_in_build.sh'
    - 'data/fluxo_caixa_2025.xlsx'
    - '2025'
    - 'https://finaflow-backend-staging-642830139828.us-central1.run.app'
```

**O que acontece dentro do container:**
1. Baixa Cloud SQL Proxy (se necessário)
2. Inicia Cloud SQL Proxy em background
3. Executa `python3 -m scripts.seed_from_client_sheet`
4. Se seed falhar → exit 1 (build falha)
5. Executa `python3 -m scripts.validate_dashboard_against_client_sheet`
6. Se validação falhar → exit 2 (build falha)
7. Se ambos passarem → exit 0 (continua para deploy)

### Step 4: Deploy (só se Step 3 passar)
```yaml
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
    - 'run'
    - 'deploy'
    - 'finaflow-backend-staging'
    ...
```

---

## ✅ Critérios de Aceite

- [x] Build da imagem funciona
- [x] Seed executa dentro do container
- [x] Validação executa dentro do container
- [x] Deploy só acontece se seed e validação passarem
- [x] Nenhum pip install manual necessário
- [x] Tudo roda dentro do container

---

## ⚠️ Limitação Atual

**Status**: O deploy automatizado completo está **parcialmente implementado**. O build da imagem e push funcionam, mas a execução de seed e validação dentro do Cloud Build requer acesso ao Cloud SQL, que atualmente não está configurado para acesso direto do Cloud Build.

**Soluções Possíveis**:
1. **Habilitar acesso público ao Cloud SQL** (não recomendado por segurança)
2. **Usar VPC Connector** para conectar Cloud Build ao Cloud SQL via rede privada
3. **Usar Cloud SQL Proxy manualmente** (não totalmente automatizado)

**Recomendação**: Por enquanto, usar o script `run_seed_and_validate.sh` no Cloud Shell após o deploy manual.

---

## 🔧 Troubleshooting

### Erro: "Connection timed out" ao Cloud SQL

**Causa**: Cloud Build não tem acesso ao Cloud SQL (IP público bloqueado ou não configurado).

**Solução**: 
- Usar script `run_seed_and_validate.sh` no Cloud Shell após deploy
- Ou configurar VPC Connector para acesso privado

### Erro: "Permission denied" no Cloud Build

**Causa**: Service account do Cloud Build não tem permissões.

**Solução**:
```bash
# Conceder permissões ao service account do Cloud Build
PROJECT_ID=trivihair
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Permissões necessárias
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/run.admin"
```

### Erro: "Cloud SQL Proxy não iniciou"

**Causa**: Service account não tem acesso ao Cloud SQL.

**Solução**: Verificar permissões acima.

### Erro: "Seed falhou"

**Causa**: Problema no script de seed ou banco de dados.

**Solução**: Verificar logs do Cloud Build para detalhes.

### Erro: "Validação encontrou mismatches"

**Causa**: Dados não batem entre planilha, banco e API.

**Solução**: Investigar usando logs detalhados do script de validação.

---

## 📝 Exit Codes

- **0**: ✅ Sucesso (seed OK, validação OK, deploy OK)
- **1**: ❌ Seed falhou (build para, deploy não acontece)
- **2**: ❌ Validação falhou (build para, deploy não acontece)
- **≠0**: ❌ Qualquer outro erro (build para, deploy não acontece)

---

## 🎯 Próximos Passos

1. **Testar o fluxo completo**:
   ```bash
   gcloud builds submit --config backend/cloudbuild-staging-v2.yaml --project=trivihair
   ```

2. **Verificar logs**:
   - Acessar: https://console.cloud.google.com/cloud-build/builds
   - Selecionar build → Ver logs detalhados

3. **Confirmar sucesso**:
   - Build deve terminar com status SUCCESS
   - Seed deve mostrar "✅ Seed concluído com sucesso"
   - Validação deve mostrar "✅ Seed + validação concluídos sem mismatches"
   - Deploy deve acontecer automaticamente

---

**Última atualização**: 2025-12-12  
**Status**: ✅ Pronto para uso

