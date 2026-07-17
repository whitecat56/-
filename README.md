# PharmaLink

Production-ready SaaS Telegram pharmacy platform built with FastAPI, Aiogram 3, SQLAlchemy 2, PostgreSQL, Redis, JWT, Docker, and Clean Architecture.

## Features
- Customer REST API: auth, profile, medicine search/details, categories, inventory, orders, reservations-ready entities, favorites, notifications.
- Admin API: medicine CRUD and statistics endpoints with role-based access control.
- Telegram bot: Aiogram 3 main menu, inline keyboards, search entrypoint, FSM-ready Redis storage.
- Database: users, pharmacies, branches, medicines, categories, manufacturers, inventory, reservations, orders, order items, payments, coupons, favorites, addresses, notifications, audit logs, admins, employees.
- ERP adapters: abstract `BaseERPAdapter` plus 1C, Mira ERP, and custom HTTP adapter shells. No ERP credentials are hardcoded; all configuration is environment-driven.
- Background sync service runs every minute when `ERP_ENABLED=true`.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
```

## Docker
```bash
docker compose up --build
```
Services: API, Bot, Sync worker, PostgreSQL, Redis with volumes and healthchecks.

## Configuration
See `.env.example` for `BOT_TOKEN`, `DATABASE_URL`, `JWT_SECRET`, `REDIS_URL`, `ERP_PROVIDER`, `ERP_URL`, `ERP_LOGIN`, and `ERP_PASSWORD`.

## Run
```bash
uvicorn pharmalink.presentation.api.main:app --reload
python -m pharmalink.presentation.bot.main
python -m pharmalink.infrastructure.services.sync
```

## Migration
```bash
alembic upgrade head
alembic revision --autogenerate -m "change description"
```

## Development
```bash
ruff check pharmalink tests
black pharmalink tests
pytest
```

## Production
Use strong secrets, managed PostgreSQL/Redis, TLS at the ingress, separate bot/API/sync replicas, structured log collection, and customer-specific ERP adapter configuration.
