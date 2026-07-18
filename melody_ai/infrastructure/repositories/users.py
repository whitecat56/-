import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from melody_ai.database.models import Profile, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_telegram(
        self, telegram_id: int, username: str | None, first_name: str | None, last_name: str | None
    ) -> User:
        user = (
            await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        ).scalar_one_or_none()
        if user:
            return user
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            referral_code=secrets.token_urlsafe(8),
        )
        user.profile = Profile(language="en", theme="dark")
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
