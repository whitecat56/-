from pydantic import BaseModel, HttpUrl


class SongDTO(BaseModel):
    provider_id: str
    title: str
    artist: str
    album: str | None = None
    genre: str | None = None
    release_date: str | None = None
    duration_seconds: int | None = None
    popularity: int | None = None
    cover_url: HttpUrl | None = None
    preview_url: HttpUrl | None = None
    service_url: HttpUrl | None = None


class SearchResponse(BaseModel):
    query: str
    total: int
    items: list[SongDTO]
