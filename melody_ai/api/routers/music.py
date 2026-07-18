from fastapi import APIRouter, Depends, Query

from melody_ai.api.dependencies import current_user
from melody_ai.application.dto.music import SearchResponse, SongDTO
from melody_ai.application.services.music_service import MusicService
from melody_ai.config.settings import get_settings
from melody_ai.infrastructure.music.providers import DeezerProvider

router = APIRouter(prefix="/music", tags=["music"])
settings = get_settings()
service = MusicService(DeezerProvider(settings.deezer_base_url))


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=25),
    user=Depends(current_user),
):
    songs = await service.search(q, limit)
    return SearchResponse(query=q, total=len(songs), items=[SongDTO(**s.__dict__) for s in songs])


@router.get("/trending", response_model=list[SongDTO])
async def trending(country: str = "US", limit: int = 10):
    return [SongDTO(**s.__dict__) for s in await service.trending(country, limit)]


@router.get("/recommendations", response_model=list[SongDTO])
async def recommendations(seed: list[str] = Query(default=[]), user=Depends(current_user)):
    return [SongDTO(**s.__dict__) for s in await service.recommend(seed, 10)]
