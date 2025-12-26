.PHONY: qa-equalizacao baseline audit help

# Variáveis
YEAR ?= 2025
BACKEND_URL ?= https://finaflow-backend-staging-642830139828.us-central1.run.app
QA_EMAIL ?= qa@finaflow.test
QA_PASSWORD ?= QaFinaflow123!
EXCEL_FILE ?= backend/data/fluxo_caixa_2025.xlsx

help:
	@echo "📊 FinaFlow - QA Equalização Excel vs Sistema"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make baseline          - Gera baseline do Excel"
	@echo "  make audit             - Executa auditoria Excel vs API"
	@echo "  make qa-equalizacao     - Executa todo o processo de equalização"
	@echo ""
	@echo "Variáveis:"
	@echo "  YEAR=$(YEAR)"
	@echo "  BACKEND_URL=$(BACKEND_URL)"
	@echo "  EXCEL_FILE=$(EXCEL_FILE)"

baseline:
	@echo "📊 Gerando baseline do Excel..."
	cd backend && python3 -m scripts.generate_baseline_excel --file $(EXCEL_FILE) --year $(YEAR)

audit:
	@echo "🔍 Executando auditoria Excel vs API..."
	cd backend && BACKEND_URL=$(BACKEND_URL) QA_EMAIL=$(QA_EMAIL) QA_PASSWORD=$(QA_PASSWORD) \
		python3 -m scripts.audit_excel_vs_api --year $(YEAR) --backend-url $(BACKEND_URL)

qa-equalizacao: baseline audit
	@echo ""
	@echo "✅ QA Equalização concluída!"
	@echo "📄 Verifique os relatórios em:"
	@echo "   - backend/artifacts/baseline_excel_$(YEAR).json"
	@echo "   - backend/artifacts/audit_report_$(YEAR).json"
	@echo "   - backend/docs/RELATORIO_EQUALIZACAO_EXCEL_SISTEMA_$(YEAR).md"
