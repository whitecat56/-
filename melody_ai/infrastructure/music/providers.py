from abc import ABC, abstractmethod
import httpx
from melody_ai.domain.entities import Song
from melody_ai.core.exceptions import ProviderUnavailableError


class MusicProvider(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[Song]: ...
    async def trending(self, country: str = "US", limit: int = 10) -> list[Song]:
        return []

    async def recognize(self, data: bytes) -> Song | None:
        return None


class DeezerProvider(MusicProvider):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def search(self, query: str, limit: int = 10) -> list[Song]:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(f"{self.base_url}/search", params={"q": query, "limit": limit})
            r.raise_for_status()
        return [
            Song(
                provider_id=f"deezer:{x['id']}",
                title=x.get("title") or "",
                artist=(x.get("artist") or {}).get("name", ""),
                album=(x.get("album") or {}).get("title"),
                duration_seconds=x.get("duration"),
                cover_url=(x.get("album") or {}).get("cover_big"),
                preview_url=x.get("preview"),
                service_url=x.get("link"),
            )
            for x in r.json().get("data", [])
        ]

    async def trending(self, country: str = "US", limit: int = 10) -> list[Song]:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(f"{self.base_url}/chart/0/tracks", params={"limit": limit})
            r.raise_for_status()
        return [
            Song(
                provider_id=f"deezer:{x['id']}",
                title=x.get("title") or "",
                artist=(x.get("artist") or {}).get("name", ""),
                album=(x.get("album") or {}).get("title"),
                duration_seconds=x.get("duration"),
                cover_url=(x.get("album") or {}).get("cover_big"),
                preview_url=x.get("preview"),
                service_url=x.get("link"),
            )
            for x in r.json().get("data", [])
        ]


class AuddRecognitionProvider:
    def __init__(self, token: str | None):
        self.token = token

    async def recognize(self, data: bytes) -> Song | None:
        if not self.token:
            raise ProviderUnavailableError("AUDD_API_TOKEN is not configured")
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://api.audd.io/",
                data={"api_token": self.token, "return": "spotify,apple_music"},
                files={"file": ("sample.ogg", data)},
            )
            r.raise_for_status()
            result = r.json().get("result")
        if not result:
            return None
        return Song(
            provider_id=f"audd:{result.get('song_link') or result.get('title')}",
            title=result.get("title", ""),
            artist=result.get("artist", ""),
            album=result.get("album"),
            release_date=None,
            service_url=result.get("song_link"),
        )
