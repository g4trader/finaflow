from app.api.auth import router as auth_router
from app.api.groups import router as groups_router
from app.api.subgroups import router as subgroups_router
from app.api.accounts import router as accounts_router
from app.api.tenants import router as tenants_router
from app.api.users import router as users_router
from app.api.reports import router as reports_router
from app.api.transactions import router as transactions_router
from app.api.forecast import router as forecast_router

def include_routers(app):
    app.include_router(auth_router)
    app.include_router(tenants_router)
    app.include_router(users_router)
    app.include_router(groups_router)
    app.include_router(subgroups_router)
    app.include_router(accounts_router)
    app.include_router(reports_router)
    app.include_router(transactions_router)
    app.include_router(forecast_router)
