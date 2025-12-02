from fastapi import FastAPI

from app.api.accounts import router as accounts_router
from app.api.auth import router as auth_router
from app.api.csv_import import router as csv_import_router
from app.api.admin_imports import router as admin_import_router
from app.api.dashboard import router as dashboard_router
from app.api.chart_accounts import router as chart_accounts_router
from app.api.forecast import router as forecast_router
from app.api.groups import router as groups_router
from app.api.lancamentos_diarios import router as lancamentos_diarios_router
from app.api.lancamentos_previstos import router as lancamentos_previstos_router
from app.api.reports import router as reports_router
from app.api.subgroups import router as subgroups_router
from app.api.tenants import router as tenants_router
from app.api.transactions import router as transactions_router
from app.api.bank_accounts import router as bank_accounts_router
from app.api.caixa import router as caixa_router
from app.api.investments import router as investments_router

# Routers baseados em BigQuery/legacy
LEGACY_ROUTERS = [
    auth_router,
    accounts_router,
    csv_import_router,
    forecast_router,
    groups_router,
    reports_router,
    subgroups_router,
    tenants_router,
    transactions_router,
    admin_import_router,
    dashboard_router,
    chart_accounts_router,
    lancamentos_diarios_router,
    lancamentos_previstos_router,
    bank_accounts_router,
    caixa_router,
    investments_router,
]


def include_routers(app: FastAPI, prefix: str = "") -> None:
    for router in LEGACY_ROUTERS:
        app.include_router(router, prefix=prefix)
