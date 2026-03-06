__all__ = ["BookService"]


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.books import Book
from src.models.sellers import Seller
from src.schemas.books import IncomingBook, PatchBook, UpdatedBook


class BookService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_book(self, book: IncomingBook) -> Book:
        # проверяем существование продавца
        query = select(Seller).where(Seller.id == book.seller_id)
        result = await self.session.execute(query)
        seller = result.scalar_one_or_none()

        if not seller:
            raise ValueError(f"Seller with id {book.seller_id} not found")

        new_book = Book(
            seller_id=book.seller_id,
            title=book.title,
            author=book.author,
            year=book.year,
            pages=book.pages,
        )

        self.session.add(new_book)
        await self.session.flush()
        return new_book

    async def delete_book(self, book_id: int) -> bool:
        book = await self.session.get(Book, book_id)

        if book:
            await self.session.delete(book)
            return True

        else:
            return False

    async def update_book(
        self, book_id: int, new_book_data: UpdatedBook
    ) -> Book | None:
        # оператор "морж", позволяющий одновременно и присвоить значение и проверить его. Заменяет то, что закомментировано выше
        if updated_book := await self.session.get(Book, book_id):
            updated_book.seller_id = new_book_data.seller_id
            updated_book.title = new_book_data.title
            updated_book.author = new_book_data.author
            updated_book.pages = new_book_data.pages
            updated_book.year = new_book_data.year

            await self.session.flush()

            return updated_book

    async def partial_update_book(
        self, book_id: int, patched_book: PatchBook
    ) -> Book | None:
        if book := await self.session.get(Book, book_id):

            if (
                patched_book.seller_id is not None
                and patched_book.seller_id != book.seller_id
            ):
                book.seller_id = patched_book.seller_id
            if patched_book.title is not None and patched_book.title != book.title:
                book.title = patched_book.title
            if patched_book.author is not None and patched_book.author != book.author:
                book.author = patched_book.author
            if patched_book.year is not None and patched_book.year != book.year:
                book.year = patched_book.year
            if patched_book.pages is not None and patched_book.pages != book.pages:
                book.pages = patched_book.pages

            await self.session.flush()
            return book

    async def get_single_book(self, book_id: int) -> Book | None:
        return await self.session.get(Book, book_id)

    async def get_all_books(self) -> list[Book]:

        query = select(Book)
        result = await self.session.execute(query)

        return result.scalars().all()
