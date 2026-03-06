import pytest
from fastapi import status
from icecream import ic
from sqlalchemy import select

from src.models.books import Book
from src.models.sellers import Seller

API_V1_BOOKS_URL_PREFIX = "/api/v1/books"


# тест на ручку, создающую книгу (требует авторизацию)
@pytest.mark.asyncio()
async def test_create_book(auth_client, test_seller: Seller):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": test_seller.id,
    }
    response = await auth_client.post(f"{API_V1_BOOKS_URL_PREFIX}/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_book_id = result_data.pop("id", None)
    assert resp_book_id is not None, "Book id not returned from endpoint"

    assert result_data == {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "pages": 300,
        "year": 2025,
        "seller_id": test_seller.id,
    }


# тест на ручку для валидации создания книги со слишком старым годом (требует авторизацию)
@pytest.mark.asyncio()
async def test_create_book_with_old_year(auth_client, test_seller: Seller):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 1986,
        "seller_id": test_seller.id,
    }
    response = await auth_client.post(f"{API_V1_BOOKS_URL_PREFIX}/", json=data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# тест на ручку, получающую список книг
@pytest.mark.asyncio()
async def test_get_books(db_session, async_client, test_seller: Seller):
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

    response = await async_client.get(f"{API_V1_BOOKS_URL_PREFIX}/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["books"]) == 2
    # проверяем интерфейс ответа, на который у нас есть контракт
    assert response.json() == {
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2021,
                "id": book.id,
                "pages": 104,
                "seller_id": test_seller.id,
            },
            {
                "title": "Mziri",
                "author": "Lermontov",
                "year": 2021,
                "id": book_2.id,
                "pages": 108,
                "seller_id": test_seller.id,
            },
        ]
    }


# тест на ручку, получающую одну книгу
@pytest.mark.asyncio()
async def test_get_single_book(db_session, async_client, test_seller: Seller):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2001,
        pages=104,
        seller_id=test_seller.id,
    )
    book_2 = Book(
        author="Lermontov",
        title="Mziri",
        year=1997,
        pages=104,
        seller_id=test_seller.id,
    )

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_BOOKS_URL_PREFIX}/{book.id}")

    assert response.status_code == status.HTTP_200_OK

    # проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2001,
        "pages": 104,
        "id": book.id,
        "seller_id": test_seller.id,
    }


# тест на ручку для валидации получения книги с некорректным ID
@pytest.mark.asyncio()
async def test_get_single_book_with_invalid_id(
    db_session, async_client, test_seller: Seller
):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2001,
        pages=104,
        seller_id=test_seller.id,
    )

    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"{API_V1_BOOKS_URL_PREFIX}/426548")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# тест на ручку, обновляющую книгу (требует авторизацию)
@pytest.mark.asyncio()
async def test_update_book(db_session, auth_client, test_seller: Seller):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2001,
        pages=104,
        seller_id=test_seller.id,
    )

    db_session.add(book)
    await db_session.flush()

    data = {
        "title": "Mziri",
        "author": "Lermontov",
        "pages": 250,
        "year": 2024,
        "seller_id": test_seller.id,
    }

    response = await auth_client.put(
        f"{API_V1_BOOKS_URL_PREFIX}/{book.id}",
        json=data,
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # проверяем, что обновились все поля
    res = await db_session.get(Book, book.id)
    assert res.title == "Mziri"
    assert res.author == "Lermontov"
    assert res.pages == 250
    assert res.year == 2024
    assert res.seller_id == test_seller.id


# тест на ручку, частично обновляющую книгу
@pytest.mark.asyncio()
async def test_partial_update_book(db_session, async_client, test_seller: Seller):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2001,
        pages=104,
        seller_id=test_seller.id,
    )

    db_session.add(book)
    await db_session.flush()

    data = {
        "title": "Mziri",
        "author": "Lermontov",
    }

    response = await async_client.patch(
        f"{API_V1_BOOKS_URL_PREFIX}/{book.id}",
        json=data,
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # проверяем, что обновились все поля
    res = await db_session.get(Book, book.id)
    assert res.title == "Mziri"
    assert res.author == "Lermontov"


# тест на ручку, удаляющую книгу
@pytest.mark.asyncio()
async def test_delete_book(db_session, async_client, test_seller: Seller):
    book = Book(
        author="Lermontov",
        title="Mtziri",
        pages=510,
        year=2024,
        seller_id=test_seller.id,
    )

    db_session.add(book)
    await db_session.flush()
    ic(book.id)

    response = await async_client.delete(f"{API_V1_BOOKS_URL_PREFIX}/{book.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    await db_session.flush()
    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 0


# тест на ручку для валидации удаления книги с некорректным ID
@pytest.mark.asyncio()
async def test_delete_book_with_invalid_book_id(
    db_session, async_client, test_seller: Seller
):
    book = Book(
        author="Lermontov",
        title="Mtziri",
        pages=510,
        year=2024,
        seller_id=test_seller.id,
    )

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_BOOKS_URL_PREFIX}/{book.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
