# GET /books - получение списка книг
# POST /books - создание
# PUT/PATCH /books/{book_id} - обновление
# GET /books/{book_id} - получение 1 книги
# DELETE /books/{book_id} - удаление

# 2xx - OK
# 3xx - Redirects
# 4xx - Client errors
# 5xx - Server errors

# CRUD - Create, Read, Update, Delete

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from icecream import ic

from src.configurations.database import create_db_and_tables, global_init
from src.routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ic("Inicializing app...")
    global_init()
    await create_db_and_tables()
    ic("App started!")
    yield


# само приложение FastAPI - именно оно запускается сервером и служит точкой входа
# в нем можно указать разные параметры для сваггера и для эндпоинтов.
app = FastAPI(
    title="Book Library App",
    description="Учебное приложение на FastAPI для МТС ШАД",
    version="0.0.1",
    responses={404: {"description": "Object not found!"}},
    default_response_class=ORJSONResponse,  # подключаем быстрый сериализатор
    lifespan=lifespan,
)


# просто пример ручки и того, как ее можно исключить из схемы сваггера
@app.get("/main", include_in_schema=False)
async def main():
    return "Hello World!"


app.include_router(api_router)
