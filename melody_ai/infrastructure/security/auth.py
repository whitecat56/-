from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from melody_ai.config.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(subject: str, roles: list[str] | None = None) -> str:
    s = get_settings()
    exp = datetime.now(UTC) + timedelta(minutes=s.jwt_expire_minutes)
    return jwt.encode(
        {"sub": subject, "roles": roles or [], "exp": exp},
        s.jwt_secret.get_secret_value(),
        algorithm=s.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    s = get_settings()
    return jwt.decode(token, s.jwt_secret.get_secret_value(), algorithms=[s.jwt_algorithm])
