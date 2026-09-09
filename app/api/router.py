from fastapi import APIRouter

from app.api.routes_agents import router as agents_router
from app.api.routes_business import router as business_router
from app.api.routes_health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(business_router)
api_router.include_router(agents_router)
