from app.api.groups import router as groups_router
from app.api.subgroups import router as subgroups_router
from app.api.accounts import router as accounts_router

def include_routers(app):
    app.include_router(groups_router)
    app.include_router(subgroups_router)
    app.include_router(accounts_router)
