# Relatório de QA – Sprint 0 (FinaFlow)

## Contexto
- **Objetivo:** validar integridade dos módulos dependentes de filtros, hierarquia contábil, token/BU e mapeamento financeiro.
- **Abrangência:** Lançamentos Financeiros e Previstos, Fluxos de Caixa (Mensal e Diário), Caixa Físico, Investimentos, autenticação e troca de Business Unit.
- **Ambiente:** Staging agora operacional com frontend `https://finaflow-lcz5.vercel.app/` e backend `https://finaflow-backend-staging-642830139828.us-central1.run.app`. Credenciais QA fornecidas: `qa@finaflow.test` / `QaFinaflow123!`. A reprovação anterior foi exclusivamente por indisponibilidade de ambiente e está sanada.

## Resumo Executivo
| Área | Resultado | Observações |
| --- | --- | --- |
| Filtros (todos os módulos) | 🚧 Não executado | Testes manuais pendentes; requere navegação UI. |
| Hierarquia Contábil | 🚧 Não executado | Depende de sessão autenticada e comparação com planilha-modelo. |
| Lançamentos (CRUD) | 🚧 Não executado | Aguardando execução manual (criar/editar/excluir previstos e realizados). |
| Business Unit / Token | 🚧 Não executado | Troca de BU e validação de isolamento aguardam verificação manual. |
| Caixa Físico e Investimentos | 🚧 Não executado | CRUD completo pendente em staging. |
| Fluxo de Caixa (Mensal/Diário) | 🚧 Não executado | Necessário validar ordenação/totais após criação de lançamentos de teste. |
| Regressão Sprint 0 | 🚧 Não executado | Login, navegação e dashboard precisam ser percorridos manualmente. |

> Status geral da Sprint 0: **REPROVADA (testes funcionais não executados; evidências pendentes)**. Ambiente já está disponível; é necessário rodar integralmente o plano `SPRINT_0_QA_PLAN.md` para deliberar aprovação.

## Evidências de Ambiente
- `https://finaflow-lcz5.vercel.app/` responde 200 OK, confirmando que o frontend de staging está publicado.【6b6c32†L1-L17】
- `https://finaflow-backend-staging-642830139828.us-central1.run.app` responde 200 OK para GET e 405 para HEAD, indicando serviço ativo em Cloud Run.【d222f0†L1-L4】【a47b76†L1-L9】 Credenciais QA disponíveis para autenticação via UI.

## Detalhamento dos Testes (todos bloqueados)
### 1. Filtros
- Validar individualmente: `start_date`, `end_date`, `group_id`, `subgroup_id`, `account_id`, `transaction_type`, `status (previsto/realizado)`, `cost_center_id` (observação futura).
- Validar combinações: grupo + conta; subgrupo + datas; conta + datas; grupo + subgrupo + datas; combinações arbitrárias.
- Módulos: Lançamentos Financeiros, Lançamentos Previstos, Fluxo de Caixa Mensal, Fluxo de Caixa Diário.
- **Status:** 🚧 Não executado – aguarda navegação UI e credenciais QA (agora disponíveis) para validar filtros isolados e combinados.

### 2. Hierarquia Contábil
- Verificar ordem grupos → subgrupos → contas, inclusão de contas faltantes e nomenclatura conforme planilha-modelo.
- Conferir ordenação vertical e agrupamentos na UI.
- **Status:** 🚧 Não executado – depende da UI e dados autenticados.

### 3. Lançamentos
- Criar, editar e remover lançamento com exibição imediata.
- Filtragem por período e separação entre previsto vs realizado.
- **Status:** 🚧 Não executado – falta execução manual com o usuário QA disponível.

### 4. Business Unit (BU)
- Trocar BU, validar isolamento de dados e atualização de token.
- Garantir que lançamentos de BU distinta não apareçam após troca.
- **Status:** 🚧 Não executado – precisa de navegação autenticada para observar token com `tenant_id` e `business_unit_id` e isolar dados.

### 5. Caixa Físico e Investimentos
- Criar, editar, listar, remover e validar persistência para ambos os módulos.
- **Status:** 🚧 Não executado – depende de login QA para operar os CRUDs.

### 6. Fluxo de Caixa
- Mensal: validar ordenação, totais e agrupamento hierárquico.
- Diário: validar ordenação, agrupamento e valores.
- **Status:** 🚧 Não executado – requer geração de lançamentos de teste e comparação na UI.

### 7. Regressão Sprint 0
- Login, troca de BU, carregamento do dashboard, navegação geral e ausência de erros silenciosos.
- **Status:** 🚧 Não executado – aguarda rodada completa de regressão agora que o ambiente está acessível.

## Ações Recomendadas
1. Percorrer o plano `SPRINT_0_QA_PLAN.md` executando os cenários de filtros, hierarquia, lançamentos (previstos e realizados), BU/token, caixa/investimentos e fluxos de caixa com o usuário QA.
2. Registrar evidências (prints ou HAR) de cada cenário validado, incluindo token com `tenant_id` e `business_unit_id` após troca de BU.
3. Atualizar este relatório com resultados por módulo (APROVADO/REPROVADO) e detalhamento de bugs encontrados, se houver.

## Conclusão
Sprint 0 segue **REPROVADA** por ausência de execução dos testes funcionais (não há evidências). A indisponibilidade de ambiente foi resolvida; é necessário rodar todo o plano de QA para deliberar aprovação.
