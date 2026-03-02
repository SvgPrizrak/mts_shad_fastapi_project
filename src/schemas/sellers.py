import re

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from .books import ReturnedBook

__all__ = [
    "PatchSeller",
    "IncomingSeller",
    "UpdatedSeller",
    "ReturnedSeller",
    "ReturnedAllSellers",
    "ReturnedSellerWithBooks",
]


# миксин с валидацией e_mail для трех методов
class EmailValidationMixin:
    @field_validator("e_mail")
    @classmethod
    def validate_email(cls, val: str):
        if val is None:
            return val

        e_mail_pattern = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"

        if not re.match(e_mail_pattern, val):
            raise PydanticCustomError(
                "Validation error", "E-mail address is incorrect!"
            )
        return val


# базовый класс "Продавец", содержащий поля, которые есть во всех классах-наследниках
class BaseSeller(BaseModel, EmailValidationMixin):
    first_name: str
    last_name: str
    e_mail: str
    password: str


# класс для обработки входных данных для частичного обновления данных о продавце
class PatchSeller(BaseModel, EmailValidationMixin):
    first_name: str | None = None
    last_name: str | None = None
    e_mail: str | None = None
    password: str | None = None


# класс для валидации входящих данных - не содержит id так как его присваивает БД - название оставил для единообразия
class IncomingSeller(BaseSeller):
    pass


# класс, предназначенный для обновления продавцов - ID продавца, пароль и список книг мы не обновляем
class UpdatedSeller(BaseModel, EmailValidationMixin):
    first_name: str
    last_name: str
    e_mail: str


# класс, валидирующий исходящие данные - он уже содержит id
class ReturnedSeller(BaseSeller):
    id: int

    # исключение пароля из возвращаемых значений - мы его не хотим видеть при выводе, ибо небезопасно
    password: str = Field(exclude=True)


# класс для возврата конкретного продавца - с книгами
class ReturnedSellerWithBooks(ReturnedSeller):
    books: list[ReturnedBook] = []


# класс для возврата массива объектов "Продавец"
class ReturnedAllSellers(BaseModel):
    sellers: list[ReturnedSeller]
