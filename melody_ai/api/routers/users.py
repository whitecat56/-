from fastapi import APIRouter, Depends

from melody_ai.api.dependencies import current_user

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
async def profile(user=Depends(current_user)):
    return {"profile": user}
