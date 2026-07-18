from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class Song:
    provider_id: str
    title: str
    artist: str
    album: str | None = None
    genre: str | None = None
    release_date: date | None = None
    duration_seconds: int | None = None
    popularity: int | None = None
    cover_url: str | None = None
    preview_url: str | None = None
    service_url: str | None = None


@dataclass(slots=True, frozen=True)
class Artist:
    provider_id: str
    name: str
    picture_url: str | None = None
    service_url: str | None = None
