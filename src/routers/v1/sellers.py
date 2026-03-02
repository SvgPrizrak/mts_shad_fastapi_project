from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.schemas import (
    IncomingSeller,
    PatchSeller,
    ReturnedAllSellers,
    ReturnedSeller,
    ReturnedSellerWithBooks,
    UpdatedSeller,
)
from src.services import SellerService

sellers_router = APIRouter(prefix="/sellers", tags=["sellers"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


@sellers_router.get("/", response_model=ReturnedAllSellers)
async def get_all_sellers(session: DBSession):
    sellers = await SellerService(session).get_all_sellers()
    return {"sellers": sellers}


@sellers_router.post(
    "/", response_model=ReturnedSeller, status_code=status.HTTP_201_CREATED
)
async def create_seller(seller: IncomingSeller, session: DBSession):
    try:
        new_seller = await SellerService(session).add_seller(seller)
        return new_seller
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)  # или 400
        )


@sellers_router.get("/{seller_id}", response_model=ReturnedSellerWithBooks)
async def get_single_seller(seller_id: int, session: DBSession):
    seller = await SellerService(session).get_single_seller(seller_id)

    if seller is not None:
        return seller

    return Response(status_code=status.HTTP_404_NOT_FOUND)


@sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: DBSession):

    deleted_seller = await SellerService(session).delete_seller(seller_id)

    if not deleted_seller:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@sellers_router.put("/{seller_id}", response_model=ReturnedSeller)
async def update_seller(
    seller_id: int, new_seller_data: UpdatedSeller, session: DBSession
):

    updated_seller = await SellerService(session).update_seller(
        seller_id, new_seller_data
    )

    if not updated_seller:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return updated_seller


@sellers_router.patch("/{seller_id}", response_model=ReturnedSeller)
async def patch_seller(seller_id: int, patched_seller: PatchSeller, session: DBSession):
    seller = await SellerService(session).partial_update_seller(
        seller_id, patched_seller
    )

    if not seller:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return seller
