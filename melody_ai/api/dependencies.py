from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from melody_ai.database.session import get_session
from melody_ai.infrastructure.security.auth import decode_token

bearer = HTTPBearer(auto_error=False)


async def db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


async def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if not creds:
        raise HTTPException(401, "Missing bearer token")
    try:
        return decode_token(creds.credentials)
    except Exception as exc:
        raise HTTPException(401, "Invalid token") from exc
