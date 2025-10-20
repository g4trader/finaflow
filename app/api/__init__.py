from app.api.auth import router as auth_router
from app.api.financial import router as financial_router

def include_routers(app):
    app.include_router(auth_router)
    app.include_router(financial_router)
