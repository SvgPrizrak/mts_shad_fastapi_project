from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.auth import get_current_user
from src.configurations.database import get_async_session
from src.models.sellers import Seller
from src.schemas import (
    IncomingBook,
    PatchBook,
    ReturnedAllBooks,
    ReturnedBook,
    UpdatedBook,
)
from src.services import BookService

books_router = APIRouter(prefix="/books", tags=["books"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


@books_router.get("/", response_model=ReturnedAllBooks)
async def get_all_books(session: DBSession):
    books = await BookService(session).get_all_books()
    return {"books": books}


@books_router.post(
    "/", response_model=ReturnedBook, status_code=status.HTTP_201_CREATED
)
async def create_book(
    book: IncomingBook,
    session: DBSession,
    current_user: Annotated[Seller, Depends(get_current_user)],
):
    try:
        # проверяем, что seller_id из запроса авторизован
        if book.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create book for this user!",
            )
        new_book = await BookService(session).add_book(book)
        return new_book
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@books_router.get("/{book_id}", response_model=ReturnedBook)
async def get_single_book(book_id: int, session: DBSession):
    book = await BookService(session).get_single_book(book_id)

    if book is not None:
        return book

    return Response(status_code=status.HTTP_404_NOT_FOUND)


@books_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, session: DBSession):

    deleted_book = await BookService(session).delete_book(book_id)

    if not deleted_book:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@books_router.put("/{book_id}", response_model=ReturnedBook)
async def update_book(
    book_id: int,
    new_book_data: UpdatedBook,
    session: DBSession,
    current_user: Annotated[Seller, Depends(get_current_user)],
):
    try:
        book_service = BookService(session)
        existing_book = await book_service.get_single_book(book_id)

        if not existing_book:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        if existing_book.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this book",
            )

        updated_book = await book_service.update_book(book_id, new_book_data)
        return updated_book

    except IntegrityError:
        # пишем, что seller_id не существует
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seller with this id does not exist",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@books_router.patch("/{book_id}", response_model=ReturnedBook)
async def patch_book(book_id: int, patched_book: PatchBook, session: DBSession):
    book = await BookService(session).partial_update_book(book_id, patched_book)

    if not book:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return book
