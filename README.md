# 🎵 MELODY AI

Enterprise-grade Telegram music discovery bot built with Python 3.12, Aiogram 3, FastAPI, PostgreSQL, Redis, SQLAlchemy 2, Alembic and Docker.

MELODY AI helps users discover songs, artists, albums, charts, legal previews, favorites, playlists, recommendations, history, premium features, referrals and admin workflows. It intentionally does **not** download copyrighted music; it integrates with legitimate metadata/preview providers.

## Features
- Beautiful Telegram UI with emoji, inline/reply keyboards, FSM, typing actions and paginated-ready flows.
- Search by song, artist, album or lyrics snippet when supported by a configured provider.
- Official metadata: cover, title, artist, album, genre, release date, duration, popularity and preview URL when available.
- Favorites, playlists, trending, recommendations, recognition hooks, settings, premium, referrals and admin-ready schema.
- REST API with JWT authentication, rate-limiting foundation, validation and typed schemas.
- Clean Architecture: domain, application, infrastructure, presentation/bot and API layers.

## Official providers
- Deezer public API is enabled by default for metadata, charts and 30-second previews where available.
- AudD can be connected for recognition with `AUDD_API_TOKEN`.
- Spotify can be connected with `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` by adding another `MusicProvider` implementation.

## Run with Docker
```bash
cp .env.example .env
# edit BOT_TOKEN and JWT_SECRET
docker compose up --build
```

## Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn melody_ai.api.app:app --reload
python -m melody_ai.bot.app
```

## Production
- Use managed PostgreSQL and Redis, strong `JWT_SECRET`, Telegram webhook deployment, horizontal API replicas and separate bot workers.
- Run `alembic upgrade head` during release.
- Configure observability collection for JSON logs emitted by Structlog.

## Architecture
- `domain`: pure entities and enums.
- `application`: DTOs and use-case services.
- `infrastructure`: music providers, repositories and security adapters.
- `database`: SQLAlchemy models and async sessions.
- `bot`: Aiogram handlers, states and keyboards.
- `api`: FastAPI routers and dependencies.
