from fastapi import APIRouter

from .auth import auth_router
from .books import books_router
from .sellers import sellers_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])

v1_router.include_router(books_router)
v1_router.include_router(sellers_router)
v1_router.include_router(auth_router)
