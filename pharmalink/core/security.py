from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from pharmalink.config.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(
    subject: str, minutes: int | None = None, days: int | None = None, token_type: str = "access"
) -> str:
    s = get_settings()
    exp = datetime.now(UTC) + (
        timedelta(days=days) if days else timedelta(minutes=minutes or s.access_token_minutes)
    )
    return jwt.encode(
        {"sub": subject, "type": token_type, "exp": exp}, s.jwt_secret, algorithm=s.jwt_algorithm
    )


def decode_token(token: str, expected_type: str = "access") -> str:
    s = get_settings()
    payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise JWTError("invalid token type")
    return str(payload["sub"])
