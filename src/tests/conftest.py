"""Это модуль с фикстурами для пайтеста.
Фикстуры - это особые функции, которые не надо импортировать явно.
Сам пайтест подтягивает их по имени из файла conftest.py
"""

import asyncio
from typing import Generator

import httpx
import pytest
import pytest_asyncio
from icecream import ic
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.configurations.auth import get_password_hash
from src.configurations.settings import settings
from src.models import books  # noqa
from src.models.base import BaseModel
from src.models.books import Book  # noqa F401
from src.models.sellers import Seller

# переопределяем движок для запуска тестов и подключаем его к тестовой базе
# это решает проблему с сохранностью данных в основной базе приложения
# фикстуры тестов их не зачистят
# и обеспечивает чистую среду для запуска тестов - в ней не будет лишних записей

async_test_engine = create_async_engine(
    settings.database_test_url,
    echo=True,
)

# создаем фабрику сессий для тестового движка
async_test_session = async_sessionmaker(
    async_test_engine, expire_on_commit=False, autoflush=False
)


# получаем цикл событий для асинхорнного потока выполнения задач
@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop()
    yield loop
    try:
        loop.close()
    except Exception as e:
        ic(e)


# создаем таблицы в тестовой БД. Предварительно удаляя старые
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables() -> None:
    """Create tables in DB."""
    async with async_test_engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.drop_all)
        await connection.run_sync(BaseModel.metadata.create_all)


# создаем сессию для БД используемую для тестов
@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with async_test_engine.connect() as connection:
        async with async_test_session(bind=connection) as session:
            yield session
            await session.rollback()


# коллбэк для переопределения сессии в приложении
@pytest.fixture(scope="function")
def override_get_async_session(db_session):
    async def _override_get_async_session():
        yield db_session

    return _override_get_async_session


# мы не можем создать 2 приложения (app) - это приведет к ошибкам
@pytest.fixture(scope="function")
def test_app(override_get_async_session):
    from src.configurations.database import get_async_session
    from src.main import app

    app.dependency_overrides[get_async_session] = override_get_async_session

    return app


# создаем асинхронного клиента для ручек
@pytest_asyncio.fixture(scope="function")
async def async_client(test_app):
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1:8000"
    ) as test_client:
        yield test_client


# фикстура тестового продавца для удобства тестирования с учетом авторизации
@pytest.fixture(scope="function")
async def test_seller(db_session):
    hashed_password = get_password_hash("test_password")

    seller = Seller(
        first_name="Test",
        last_name="Seller",
        e_mail="test_seller@example.com",
        password=hashed_password,
    )
    db_session.add(seller)
    await db_session.flush()
    return seller


# фикстура для получения токена
@pytest_asyncio.fixture(scope="function")
async def auth_token(async_client, test_seller):
    login_data = {"email": test_seller.e_mail, "password": "test_password"}
    response = await async_client.post("/api/v1/token/", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return token


# фикстура для клиента с автоматическим токеном
@pytest_asyncio.fixture(scope="function")
async def auth_client(async_client, auth_token):
    async_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return async_client
