# Plano de QA – Sprint 0 (FinaFlow)

## 1) Contexto e Referências
- **Objetivo:** validar a Sprint 0 baseada nas correções aplicadas no backend (commit de referência 8274db5) para filtros, hierarquia contábil, módulos de Caixa/Investimentos, token/BU e previsões.
- **Documentos base:**
  - `SPRINT_0_CORRECOES_APLICADAS.md` (escopo técnico das correções).
  - `STAGING_SETUP.md`, `STAGING_DEPLOY_INSTRUCTIONS.md` e `scripts/create-staging.sh` (somente leitura para entender a arquitetura; execução bloqueada até liberação de permissões GCP/trivihair).
- **Premissas:**
  - URLs de backend (Cloud Run) e frontend (Vercel) de **staging** ainda não fornecidas.
  - Nenhum teste funcional deve ser marcado como executado até as URLs e credenciais estarem disponíveis.

## 2) Preparação (pré-staging)
1. Revisar `SPRINT_0_CORRECOES_APLICADAS.md` para mapear endpoints e filtros corrigidos.
2. Ler `STAGING_SETUP.md` e `STAGING_DEPLOY_INSTRUCTIONS.md` para compreender topologia, variáveis e comandos (não executar scripts de deploy no ambiente atual).
3. Validar que os checklists abaixo estão prontos para execução assim que os endpoints de staging forem liberados.

## 3) Escopo de Testes Funcionais (a executar quando o staging estiver disponível)

### A. Filtros (Lançamentos Financeiros, Lançamentos Previstos, Fluxo de Caixa Mensal e Diário)
**Cobertura obrigatória:**
- Filtros isolados: `grupo`, `subgrupo`, `conta`, `data inicial`, `data final`, `tipo` (receita/despesa), `status` (previsto/realizado).
- Combinações: `grupo + conta`; `subgrupo + datas`; `conta + datas`; `grupo + subgrupo + datas`; quaisquer combinações múltiplas.
- Critérios: filtro não deve "grudar" em outro; resultados devem respeitar hierarquia e valores esperados; respostas sem erro 500.

**Procedimento geral por módulo:**
1. Autenticar e capturar token com `business_unit_id` válido.
2. Aplicar cada filtro isoladamente e validar:
   - Retorno HTTP 200.
   - Lista não vazia quando dados existirem; vazia apenas quando filtro for realmente restritivo.
   - Ordenação coerente com plano de contas quando aplicável.
3. Repetir para combinações listadas acima.
4. Registrar evidências (payloads e respostas) para cada cenário.

### B. Hierarquia do Plano de Contas
- Confirmar estrutura `grupo → subgrupo → conta` e ordenação por código.
- Verificar inclusão de contas órfãs e nomenclatura conforme planilha-modelo.
- Validar exibição na UI e no endpoint `/api/v1/chart-accounts/hierarchy`.
- Evidenciar com captura/screenshot e amostra de resposta JSON.

### C. Lançamentos (Previstos e Realizados)
- Criar lançamento manual (previsto e realizado) e verificar exibição imediata.
- Editar lançamento e confirmar atualização na listagem.
- Remover e garantir remoção imediata da UI/endpoint.
- Aplicar filtros por período e tipo (`transaction_type`, `status`).
- Validar separação entre previsto vs realizado no endpoint `/cash-flow/previsto-realizado`.

### D. Business Unit / Token
- Autenticar, selecionar BU e confirmar que o token inclui `business_unit_id`.
- Trocar de BU e verificar isolamento de dados (lancamentos, caixa, investimentos e fluxos não devem vazar entre BUs).
- Reexecutar filtros após troca para garantir escopo correto.

### E. Caixa Físico e Investimentos
- Criar, editar, listar e remover registros em `/api/v1/caixa` e `/api/v1/investimentos`.
- Checar persistência após refresh/relogin e ausência de erro 500.
- Validar filtros de `tenant_id` e `business_unit_id` (dados devem ser restritos à BU ativa).

### F. Fluxo de Caixa (Mensal e Diário)
- Validar ordenação por grupo/subgrupo/conta.
- Conferir totais e agrupamento hierárquico nos endpoints `/financial/cash-flow` (mensal) e `/cash-flow/daily` (diário).
- Cross-check com lançamentos criados/fixtures conhecidos.

### G. Regressão Sprint 0
- Login (fluxo completo) e carregamento do dashboard inicial.
- Navegação entre menus e ausência de erros silenciosos no console/network.
- Troca de BU e revalidação de dados visíveis em cada módulo.

## 4) Critérios de Aceite
- Todos os filtros funcionam isolada e combinadamente em todos os módulos listados.
- Hierarquia contábil correta e completa (sem contas ausentes ou órfãs não exibidas).
- CRUD de lançamentos, caixa e investimentos persistem e respeitam `tenant_id`/`business_unit_id`.
- Token/BU funcional em todo o fluxo, sem vazamento de dados entre BUs.
- Fluxos de caixa (mensal/diário) com ordenação e totais alinhados aos lançamentos.
- Regressão básica sem erros (login, dashboard, navegação).

## 5) Evidências e Relatórios
- Registrar requisições/respostas (payload + status) e capturas de tela onde aplicável.
- Consolidar resultados no arquivo `SPRINT_0_QA_REPORT.md` com status **APROVADO** ou **REPROVADO**, listando cenários testados e defeitos (módulo, cenário, esperado, obtido, prioridade).
- Caso o staging permaneça indisponível, documentar explicitamente: "Não testado: aguardando URL de STAGING" para cada bloco funcional.

## 6) Checklist de Desbloqueio (Staging)
- Receber URLs de backend (Cloud Run) e frontend (Vercel) de staging.
- Obter credenciais/usuário de teste e confirmar escopos de `business_unit_id`.
- Validar que os scripts de staging (`create-staging.sh`) não necessitam execução pelo QA; apenas leitura para compreensão.
- Após desbloqueio, executar todas as seções A–G e atualizar `SPRINT_0_QA_REPORT.md` com os resultados.
