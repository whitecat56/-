from fastapi import APIRouter
from pydantic import BaseModel

from melody_ai.infrastructure.security.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/token")
async def token(payload: LoginRequest):
    # Integrate enterprise SSO/password table in production deployments.
    return {"access_token": create_access_token(payload.username, ["user"]), "token_type": "bearer"}
