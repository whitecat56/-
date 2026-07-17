from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from pharmalink.infrastructure.database.models import Inventory, Medicine, Order, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: int):
        return await self.session.get(User, user_id)

    async def by_login(self, login: str):
        return (
            await self.session.execute(
                select(User).where(or_(User.email == login, User.phone == login))
            )
        ).scalar_one_or_none()

    async def add(self, user: User):
        self.session.add(user)
        await self.session.flush()
        return user


class MedicineRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, q: str, limit: int = 20):
        like = f"%{q}%"
        res = await self.session.execute(
            select(Medicine)
            .where(
                Medicine.is_active.is_(True),
                or_(
                    Medicine.name.ilike(like),
                    Medicine.barcode == q,
                    Medicine.active_ingredient.ilike(like),
                ),
            )
            .limit(limit)
        )
        return list(res.scalars())

    async def get(self, mid: int):
        return await self.session.get(Medicine, mid)

    async def add(self, med: Medicine):
        self.session.add(med)
        await self.session.flush()
        return med

    async def delete(self, med: Medicine):
        med.is_active = False
        await self.session.flush()


class InventoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def by_medicine(self, medicine_id: int):
        return list(
            (
                await self.session.execute(
                    select(Inventory).where(Inventory.medicine_id == medicine_id)
                )
            ).scalars()
        )

    async def get_for_update(self, branch_id: int, medicine_id: int):
        return (
            await self.session.execute(
                select(Inventory)
                .where(Inventory.branch_id == branch_id, Inventory.medicine_id == medicine_id)
                .with_for_update()
            )
        ).scalar_one_or_none()


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, order: Order):
        self.session.add(order)
        await self.session.flush()
        return order
