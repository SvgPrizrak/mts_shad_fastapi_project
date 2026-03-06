from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.auth import create_access_token, verify_password
from src.configurations.database import get_async_session
from src.models.sellers import Seller
from src.schemas.auth import LoginRequest, Token

auth_router = APIRouter(prefix="/token", tags=["authentication"])


@auth_router.post("/", response_model=Token)
async def login(
    login_data: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    # ищем продавца по email
    query = select(Seller).where(Seller.e_mail == login_data.email)
    result = await session.execute(query)
    seller = result.scalar_one_or_none()

    # проверяем пароль
    if not seller or not verify_password(login_data.password, seller.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # создаем токен
    access_token = create_access_token(data={"sub": seller.e_mail})
    return Token(access_token=access_token)
