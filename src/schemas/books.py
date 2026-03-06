from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

__all__ = [
    "PatchBook",
    "IncomingBook",
    "UpdatedBook",
    "ReturnedBook",
    "ReturnedAllBooks",
]


# базовый класс "Книги", содержащий поля, которые есть во всех классах-наследниках
class BaseBook(BaseModel):
    seller_id: int
    title: str
    author: str
    year: int


# класс для обработки входных данных для частичного обновления данных о книге
class PatchBook(BaseModel):
    seller_id: int | None = None
    title: str | None = None
    author: str | None = None
    year: int | None = None
    pages: int | None = None


# класс для валидации входящих данных - не содержит id так как его присваивает БД
class IncomingBook(BaseBook):
    pages: int = Field(
        default=100, alias="count_pages"
    )  # пример использования тонкой настройки полей и передачи в них метаинформации

    @field_validator("year")  # валидатор, проверяет что дата не слишком древняя
    @staticmethod
    def validate_year(val: int):
        if val < 2020:
            raise PydanticCustomError("Validation error", "Year is too old!")

        return val


# класс, предназначенный для обновления книг - для тестирования в api_tests.http больше не требуется вводить ID книги вручную
# поскольку добавился ID продавца, то мы его также можем менять - на случай смены продавца (но при его смене потребуется новый токен)
class UpdatedBook(BaseModel):
    seller_id: int | None = None
    title: str | None = None
    author: str | None = None
    year: int | None = None
    pages: int | None = None


# класс, валидирующий исходящие данные - он уже содержит id
class ReturnedBook(BaseBook):
    id: int
    pages: int


# класс для возврата массива объектов "Книга"
class ReturnedAllBooks(BaseModel):
    books: list[ReturnedBook]
