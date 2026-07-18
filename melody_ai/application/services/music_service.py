from melody_ai.domain.entities import Song
from melody_ai.infrastructure.music.providers import AuddRecognitionProvider, MusicProvider


class MusicService:
    def __init__(self, provider: MusicProvider, recognizer: AuddRecognitionProvider | None = None):
        self.provider = provider
        self.recognizer = recognizer

    async def search(self, query: str, limit: int = 10) -> list[Song]:
        return await self.provider.search(query.strip(), limit)

    async def trending(self, country: str = "US", limit: int = 10) -> list[Song]:
        return await self.provider.trending(country, limit)

    async def recommend(self, seeds: list[str], limit: int = 10) -> list[Song]:
        return await self.search(" ".join(seeds[:3]) or "top hits", limit)

    async def recognize(self, data: bytes) -> Song | None:
        if not self.recognizer:
            return None
        return await self.recognizer.recognize(data)
