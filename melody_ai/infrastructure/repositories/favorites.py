from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from melody_ai.database.models import FavoriteSong
from melody_ai.domain.entities import Song


class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, song: Song) -> None:
        self.session.add(
            FavoriteSong(
                user_id=user_id,
                provider_id=song.provider_id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                cover_url=song.cover_url,
                preview_url=song.preview_url,
                service_url=song.service_url,
            )
        )
        await self.session.commit()

    async def remove(self, user_id: int, provider_id: str) -> None:
        await self.session.execute(
            delete(FavoriteSong).where(
                FavoriteSong.user_id == user_id, FavoriteSong.provider_id == provider_id
            )
        )
        await self.session.commit()

    async def list(self, user_id: int, offset: int = 0, limit: int = 10):
        return (
            (
                await self.session.execute(
                    select(FavoriteSong)
                    .where(FavoriteSong.user_id == user_id)
                    .order_by(FavoriteSong.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
