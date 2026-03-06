import pytest
from fastapi import status
from icecream import ic
from sqlalchemy import select

from src.models.books import Book
from src.models.sellers import Seller

API_V1_BOOKS_URL_PREFIX = "/api/v1/books"
API_V1_SELLERS_URL_PREFIX = "/api/v1/sellers"


# тест на ручку, создающую продавца
@pytest.mark.asyncio()
async def test_create_seller(
    async_client, test_seller: Seller, e_mail="test_seller_1@example.com"
):
    data = {
        "first_name": test_seller.first_name,
        "last_name": test_seller.last_name,
        "e_mail": e_mail,  # заменил e_mail, чтобы не было ошибки 409 с дубликатом e_mail
        "password": test_seller.password,
    }
    response = await async_client.post(f"{API_V1_SELLERS_URL_PREFIX}/", json=data)

    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()
    seller_id = result.pop("id", None)
    assert seller_id is not None
    assert result == {
        "first_name": test_seller.first_name,
        "last_name": test_seller.last_name,
        "e_mail": e_mail,
    }


# тест на ручку для валидации создания продавца со некорректным ID (не создает, не падает с ошибкой)
@pytest.mark.asyncio()
async def test_create_seller_with_invalid_email(async_client):
    data = {
        "first_name": "Jim",
        "last_name": "Carey",
        "e_mail": "invalid-email",
        "password": "the_mask",
    }
    response = await async_client.post(f"{API_V1_SELLERS_URL_PREFIX}/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# тест на ручку для валидации создания продавца со некорректным e-mail (не создает, не падает с ошибкой)
@pytest.mark.asyncio()
async def test_create_seller_with_duplicate_email(
    async_client, e_mail="original_guy@gmail.com"
):
    seller_data = {
        "first_name": "Original",
        "last_name": "Guy",
        "e_mail": e_mail,
        "password": "pass1",
    }

    response = await async_client.post(
        f"{API_V1_SELLERS_URL_PREFIX}/", json=seller_data
    )
    assert response.status_code == status.HTTP_201_CREATED

    seller_duplicate_data = {
        "first_name": "Clone",
        "last_name": "Guy",
        "e_mail": e_mail,
        "password": "pass2",
    }

    response = await async_client.post(
        f"{API_V1_SELLERS_URL_PREFIX}/", json=seller_duplicate_data
    )
    assert response.status_code == 409


# тест на ручку, получающую одного продавца (требует авторизацию)
@pytest.mark.asyncio()
async def test_get_seller(auth_client, test_seller: Seller):
    response = await auth_client.get(f"{API_V1_SELLERS_URL_PREFIX}/{test_seller.id}")
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result == {
        "id": test_seller.id,
        "first_name": test_seller.first_name,
        "last_name": test_seller.last_name,
        "e_mail": test_seller.e_mail,
        "books": [],
    }


# тест на ручку, получающую список продавцов
@pytest.mark.asyncio()
async def test_get_sellers(db_session, async_client, test_seller: Seller):

    test_seller_2 = Seller(
        first_name="Test2",
        last_name="Seller2",
        e_mail="test_seller2@example2.com",
        password="test_password2",
    )

    db_session.add(test_seller_2)
    await db_session.flush()

    response = await async_client.get(f"{API_V1_SELLERS_URL_PREFIX}/")

    assert response.status_code == status.HTTP_200_OK

    # проверяем интерфейс ответа, на который у нас есть контракт
    assert response.json() == {
        "sellers": [
            {
                "id": test_seller.id,
                "first_name": test_seller.first_name,
                "last_name": test_seller.last_name,
                "e_mail": test_seller.e_mail,
            },
            {
                "id": test_seller_2.id,
                "first_name": test_seller_2.first_name,
                "last_name": test_seller_2.last_name,
                "e_mail": test_seller_2.e_mail,
            },
        ]
    }


# тест на ручку для валидации получения продавца с некорректным ID (не получает, не падает с ошибкой, требует авторизацию)
@pytest.mark.asyncio()
async def test_get_seller_with_invalid_id(auth_client):
    response = await auth_client.get(f"{API_V1_SELLERS_URL_PREFIX}/-1")
    assert response.status_code == status.HTTP_403_FORBIDDEN


# тест на ручку, получающую продавца со списком книг (требует авторизацию)
@pytest.mark.asyncio()
async def test_get_seller_with_books(auth_client, db_session, test_seller: Seller):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2021,
        pages=104,
        seller_id=test_seller.id,
    )

    book_2 = Book(
        author="Lermontov",
        title="Mziri",
        year=2021,
        pages=108,
        seller_id=test_seller.id,
    )

    db_session.add_all([book, book_2])
    await db_session.flush()

    books_response = await auth_client.get(f"{API_V1_BOOKS_URL_PREFIX}/")
    assert books_response.status_code == status.HTTP_200_OK
    books_result = books_response.json()

    sellers_response = await auth_client.get(
        f"{API_V1_SELLERS_URL_PREFIX}/{test_seller.id}"
    )
    assert sellers_response.status_code == status.HTTP_200_OK
    sellers_result = sellers_response.json()

    assert sellers_result == {
        "id": test_seller.id,
        "first_name": test_seller.first_name,
        "last_name": test_seller.last_name,
        "e_mail": test_seller.e_mail,
        **books_result,
    }


# тест на ручку, получающую полностью обновленного продавца (без ID)
@pytest.mark.asyncio()
async def test_update_seller(async_client, test_seller: Seller):
    data = {
        "first_name": "Updated",
        "last_name": "Guy",
        "e_mail": "updated_guy@example.com",
        "password": "updated_pass",
    }
    response = await async_client.put(
        f"{API_V1_SELLERS_URL_PREFIX}/{test_seller.id}", json=data
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    seller_id = result.pop("id", None)
    assert seller_id is not None
    assert result == {
        "first_name": "Updated",
        "last_name": "Guy",
        "e_mail": "updated_guy@example.com",
    }


# тест на ручку для валидации полного обновления книги с некорректным e-mail (не обновляет, не падает с ошибкой)
@pytest.mark.asyncio()
async def test_update_seller_invalid_email(async_client, test_seller: Seller):
    data = {
        "first_name": "Updated",
        "last_name": "Guy",
        "e_mail": "invalid-email",
        "password": "new_password",
    }
    response = await async_client.put(
        f"{API_V1_SELLERS_URL_PREFIX}/{test_seller.id}", json=data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# тест на ручку, получающую частично обновленного продавца (без ID)
@pytest.mark.asyncio()
async def test_partial_update_seller(async_client, test_seller: Seller):
    data = {
        "first_name": "Updated",
        "last_name": "Guy",
        "password": "new_password",  # даже если мы попробуем поменять пароль, то он все равно не поменяется
    }
    response = await async_client.patch(
        f"{API_V1_SELLERS_URL_PREFIX}/{test_seller.id}", json=data
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    seller_id = result.pop("id", None)
    assert seller_id is not None
    assert result == {
        "first_name": "Updated",
        "last_name": "Guy",
        "e_mail": test_seller.e_mail,
    }


# тест на ручку для валидации частичного обновления книги с некорректным e-mail (не обновляет, не падает с ошибкой)
@pytest.mark.asyncio()
async def test_partial_update_seller_with_invalid_email(
    async_client, test_seller: Seller
):
    data = {
        "first_name": "Updated",
        "last_name": "Guy",
        "e_mail": "invalid-email",
    }
    response = await async_client.patch(
        f"{API_V1_SELLERS_URL_PREFIX}/{test_seller.id}", json=data
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# тест на ручку, удаляющую продавца
@pytest.mark.asyncio()
async def test_delete_seller(db_session, async_client, test_seller: Seller):
    db_session.add(test_seller)
    await db_session.flush()
    ic(test_seller.id)

    response = await async_client.delete(
        f"{API_V1_SELLERS_URL_PREFIX}/{test_seller.id}"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()
    all_sellers = await db_session.execute(select(Seller))
    res = all_sellers.scalars().all()

    assert len(res) == 0


# тест на ручку для валидации удаления продавца с некорректным ID (не удаляет, не падает с ошибкой)
@pytest.mark.asyncio()
async def test_delete_seller_with_invalid_id(
    db_session, async_client, test_seller: Seller
):
    db_session.add(test_seller)
    await db_session.flush()

    response = await async_client.delete(
        f"{API_V1_SELLERS_URL_PREFIX}/{test_seller.id + 1}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# тест на ручку, удаляющую продавца единовременно со списком книг
@pytest.mark.asyncio()
async def test_delete_seller_with_books(db_session, async_client, test_seller: Seller):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2021,
        pages=104,
        seller_id=test_seller.id,
    )
    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(
        f"{API_V1_SELLERS_URL_PREFIX}/{test_seller.id}"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()

    all_sellers = await db_session.execute(select(Seller))
    sellers = all_sellers.scalars().all()
    assert len(sellers) == 0

    all_books = await db_session.execute(select(Book))
    books = all_books.scalars().all()
    assert len(books) == 0
