__all__ = ["SellerService"]


from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.sellers import Seller
from src.schemas.sellers import IncomingSeller, PatchSeller, UpdatedSeller


class SellerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_seller(self, seller: IncomingSeller) -> Seller:
        # это - бизнес логика. Обрабатываем данные, сохраняем, преобразуем и т.д.
        new_seller = Seller(
            **{
                "first_name": seller.first_name,
                "last_name": seller.last_name,
                "e_mail": seller.e_mail,
                "password": seller.password,
            }
        )

        try:
            self.session.add(new_seller)
            await self.session.flush()
            return new_seller
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("Account with this e-mail already exists!")

    async def delete_seller(self, seller_id: int) -> bool:
        seller = await self.session.get(Seller, seller_id)

        if seller:
            await self.session.delete(seller)
            return True

        else:
            return False

    async def update_seller(
        self, seller_id: int, new_seller_data: UpdatedSeller
    ) -> Seller | None:
        # Оператор "морж", позволяющий одновременно и присвоить значение и проверить его. Заменяет то, что закомментировано выше.
        if updated_seller := await self.session.get(Seller, seller_id):
            updated_seller.first_name = new_seller_data.first_name
            updated_seller.last_name = new_seller_data.last_name
            updated_seller.e_mail = new_seller_data.e_mail

            await self.session.flush()

            return updated_seller

    async def partial_update_seller(
        self, seller_id: int, patched_seller: PatchSeller
    ) -> Seller | None:
        if seller := await self.session.get(Seller, seller_id):

            if (
                patched_seller.first_name is not None
                and patched_seller.first_name != seller.first_name
            ):
                seller.first_name = patched_seller.first_name
            if (
                patched_seller.last_name is not None
                and patched_seller.last_name != seller.last_name
            ):
                seller.last_name = patched_seller.last_name
            if (
                patched_seller.e_mail is not None
                and patched_seller.e_mail != seller.e_mail
            ):
                seller.e_mail = patched_seller.e_mail
            if (
                patched_seller.password is not None
                and patched_seller.password != seller.password
            ):
                seller.password = patched_seller.password

            await self.session.flush()
            return seller

    async def get_single_seller(self, seller_id: int) -> Seller | None:
        query = (
            select(Seller)
            .where(Seller.id == seller_id)
            .options(selectinload(Seller.books))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_sellers(self) -> list[Seller]:
        query = select(Seller)
        result = await self.session.execute(
            query
        )  # await session.execute(select(Seller))

        return result.scalars().all()
