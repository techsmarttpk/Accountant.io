from fastapi import APIRouter, Depends

from app.api.v1 import calculations, chat, documents, health, users
from app.core.security import verify_internal_api_key

api_router = APIRouter()
api_router.include_router(health.router)

protected_router = APIRouter(dependencies=[Depends(verify_internal_api_key)])
protected_router.include_router(users.router)
protected_router.include_router(documents.router)
protected_router.include_router(calculations.router)
protected_router.include_router(chat.router)

api_router.include_router(protected_router)
