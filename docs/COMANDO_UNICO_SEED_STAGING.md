# 🚀 Comando Único - Seed STAGING

**Método**: Cloud SQL Proxy + Script Automático  
**Ambiente**: Cloud Shell  
**Tempo estimado**: 5-10 minutos

---

## ⚡ EXECUTAR NO CLOUD SHELL (STAGING - FinaFlow)

```bash
gcloud config set project trivihair
curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_seed_with_proxy.sh | bash
```

---

## ✅ O QUE O SCRIPT FAZ

1. ✅ Configura projeto gcloud (`trivihair`)
2. ✅ Baixa e inicia Cloud SQL Proxy
3. ✅ Clona repositório (branch `staging`)
4. ✅ Instala dependências (requirements.txt, pandas, openpyxl)
5. ✅ Configura DATABASE_URL (via proxy local: `127.0.0.1:5432`)
6. ✅ Executa seed (primeira vez) - cria dados
7. ✅ Executa seed (segunda vez) - valida idempotência
8. ✅ Exibe estatísticas resumidas
9. ✅ Para Cloud SQL Proxy automaticamente

---

## 📊 RESULTADO ESPERADO

### Primeira Execução
- Mensagem: "🌱 INICIANDO SEED DO AMBIENTE STAGING"
- Estatísticas mostram itens **"criados"**
- Mensagem: "✅ SEED CONCLUÍDO COM SUCESSO!"

### Segunda Execução (Idempotência)
- Estatísticas mostram itens **"existentes"** (não "criados")
- Nenhum registro duplicado criado

### Estatísticas Exibidas
- Grupos: X criados, Y existentes
- Subgrupos: X criados, Y existentes
- Contas: X criadas, Y existentes
- Lançamentos Diários: X criados, Y existentes
- Lançamentos Previstos: X criados, Y existentes
- Linhas ignoradas: Z

---

## 📝 PRÓXIMOS PASSOS

Após rodar o comando acima:

1. **Validar resultado**: Verificar `docs/SEED_STAGING_STATUS.md`
2. **Executar QA funcional**: Seguir `docs/CHECKLIST_QA_FUNCIONAL_POS_SEED.md`
3. **Validar no frontend**: https://finaflow-lcz5.vercel.app/

---

## 🚨 TROUBLESHOOTING

### Erro: "Connection refused"
- Verificar se Cloud SQL Proxy iniciou corretamente
- Aguardar 5 segundos após iniciar proxy

### Erro: "Arquivo não encontrado"
- O script clona o repositório automaticamente
- Verificar: `ls -lh ~/finaflow/backend/data/fluxo_caixa_2025.xlsx`

### Erro: "pandas não instalado"
- O script instala automaticamente
- Se falhar, executar manualmente: `pip3 install pandas openpyxl`

---

**Status**: ✅ **PRONTO PARA EXECUÇÃO**

**Comando único**: Copiar e colar no Cloud Shell

