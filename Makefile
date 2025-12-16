.PHONY: e2e e2e-backend e2e-frontend

# E2E completo: Backend + Frontend
e2e: e2e-backend e2e-frontend

# E2E Backend: Planilha → API
e2e-backend:
	@echo "🚀 Executando E2E Backend (Planilha → API)..."
	@cd backend && ./scripts/run_e2e_sheet_to_api.sh --year 2025

# E2E Frontend: API → UI
e2e-frontend:
	@echo "🚀 Executando E2E Frontend (API → UI)..."
	@cd frontend && npm run e2e:consistency

