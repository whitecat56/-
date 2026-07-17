from fastapi import Depends, FastAPI, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pharmalink.application.schemas import (
    LoginRequest,
    MedicineCreate,
    OrderCreate,
    RegisterRequest,
    TokenPair,
    UserRead,
)
from pharmalink.application.services import AuthService, MedicineService, OrderService
from pharmalink.core.logging import configure_logging
from pharmalink.domain.enums import UserRole
from pharmalink.infrastructure.database.models import (
    Category,
    Favorite,
    Inventory,
    Medicine,
    Notification,
    User,
)
from pharmalink.infrastructure.database.session import get_session
from pharmalink.presentation.api.dependencies import current_user, require_roles

configure_logging()
app = FastAPI(title="PharmaLink API", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserRead)
async def register(data: RegisterRequest, session: AsyncSession = Depends(get_session)):
    return await AuthService(session).register(data)


@app.post("/auth/login", response_model=TokenPair)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)):
    access, refresh = await AuthService(session).login(data.username, data.password)
    return TokenPair(access_token=access, refresh_token=refresh)


@app.post("/auth/refresh", response_model=TokenPair)
async def refresh(refresh_token: str = Query(...)):
    from pharmalink.core.security import create_token, decode_token

    uid = decode_token(refresh_token, "refresh")
    return TokenPair(
        access_token=create_token(uid),
        refresh_token=create_token(uid, days=14, token_type="refresh"),
    )


@app.get("/profile", response_model=UserRead)
async def profile(user: User = Depends(current_user)):
    return user


@app.get("/medicines")
async def medicine_search(q: str, session: AsyncSession = Depends(get_session)):
    return await MedicineService(session).search(q)


@app.get("/medicines/{medicine_id}")
async def medicine_details(medicine_id: int, session: AsyncSession = Depends(get_session)):
    return await session.get(Medicine, medicine_id)


@app.get("/categories")
async def categories(session: AsyncSession = Depends(get_session)):
    return list((await session.execute(select(Category))).scalars())


@app.get("/inventory/{medicine_id}")
async def inventory(medicine_id: int, session: AsyncSession = Depends(get_session)):
    return list(
        (
            await session.execute(select(Inventory).where(Inventory.medicine_id == medicine_id))
        ).scalars()
    )


@app.post("/orders")
async def create_order(
    data: OrderCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    return await OrderService(session).create_order(user.id, data)


@app.get("/favorites")
async def favorites(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
):
    return list(
        (await session.execute(select(Favorite).where(Favorite.user_id == user.id))).scalars()
    )


@app.post("/favorites/{medicine_id}")
async def add_favorite(
    medicine_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    session.add(Favorite(user_id=user.id, medicine_id=medicine_id))
    await session.commit()
    return {"status": "added"}


@app.get("/notifications")
async def notifications(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
):
    return list(
        (
            await session.execute(select(Notification).where(Notification.user_id == user.id))
        ).scalars()
    )


@app.post(
    "/admin/medicines", dependencies=[Depends(require_roles(UserRole.admin, UserRole.employee))]
)
async def admin_create_medicine(data: MedicineCreate, session: AsyncSession = Depends(get_session)):
    return await MedicineService(session).create(data)


@app.put(
    "/admin/medicines/{medicine_id}",
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.employee))],
)
async def admin_update_medicine(
    medicine_id: int, data: MedicineCreate, session: AsyncSession = Depends(get_session)
):
    med = await session.get(Medicine, medicine_id)
    [setattr(med, k, v) for k, v in data.model_dump().items()]
    await session.commit()
    return med


@app.delete("/admin/medicines/{medicine_id}", dependencies=[Depends(require_roles(UserRole.admin))])
async def admin_delete_medicine(medicine_id: int, session: AsyncSession = Depends(get_session)):
    med = await session.get(Medicine, medicine_id)
    med.is_active = False
    await session.commit()
    return {"status": "deleted"}


@app.get(
    "/admin/statistics", dependencies=[Depends(require_roles(UserRole.admin, UserRole.employee))]
)
async def statistics():
    return {"orders": 0, "reservations": 0, "revenue": 0}
