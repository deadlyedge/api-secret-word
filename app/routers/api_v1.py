from fastapi import APIRouter

from app.routers import secrets, verify

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(verify.router)
api_router.include_router(secrets.router)
