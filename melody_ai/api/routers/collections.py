from fastapi import APIRouter, Depends

from melody_ai.api.dependencies import current_user

router = APIRouter(tags=["collections"])


@router.get("/favorites")
async def favorites(user=Depends(current_user)):
    return {"items": [], "pagination": {"offset": 0, "limit": 10}}


@router.get("/playlists")
async def playlists(user=Depends(current_user)):
    return {"items": []}


@router.get("/history")
async def history(user=Depends(current_user)):
    return {"items": []}


@router.get("/statistics")
async def statistics(user=Depends(current_user)):
    return {"users": 0, "searches": 0, "premium": 0}
