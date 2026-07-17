from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from pharmalink.application.schemas import MedicineCreate, OrderCreate, RegisterRequest
from pharmalink.core.security import create_token, hash_password, verify_password
from pharmalink.domain.enums import UserRole
from pharmalink.infrastructure.database.models import Medicine, Order, OrderItem, User
from pharmalink.infrastructure.database.repositories import (
    InventoryRepository,
    MedicineRepository,
    OrderRepository,
    UserRepository,
)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.users = UserRepository(session)
        self.session = session

    async def register(self, data: RegisterRequest):
        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=UserRole.customer,
        )
        await self.users.add(user)
        await self.session.commit()
        return user

    async def login(self, username: str, password: str):
        user = await self.users.by_login(username)
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
        return create_token(str(user.id)), create_token(str(user.id), days=14, token_type="refresh")


class MedicineService:
    def __init__(self, session: AsyncSession):
        self.repo = MedicineRepository(session)
        self.session = session

    async def search(self, q: str):
        return await self.repo.search(q)

    async def create(self, data: MedicineCreate):
        med = await self.repo.add(Medicine(**data.model_dump()))
        await self.session.commit()
        return med


class OrderService:
    def __init__(self, session: AsyncSession):
        self.inventory = InventoryRepository(session)
        self.orders = OrderRepository(session)
        self.session = session

    async def create_order(self, user_id: int, data: OrderCreate):
        total = Decimal("0")
        order = Order(
            user_id=user_id,
            branch_id=data.branch_id,
            fulfillment_type=data.fulfillment_type,
            total_amount=0,
        )
        for item in data.items:
            inv = await self.inventory.get_for_update(data.branch_id, item.medicine_id)
            if not inv or inv.quantity - inv.reserved_quantity < item.quantity:
                raise HTTPException(409, f"Insufficient stock for medicine {item.medicine_id}")
            inv.reserved_quantity += item.quantity
            total += inv.price * item.quantity
            order.items.append(
                OrderItem(
                    medicine_id=item.medicine_id, quantity=item.quantity, unit_price=inv.price
                )
            )
        order.total_amount = total
        await self.orders.add(order)
        await self.session.commit()
        return order
