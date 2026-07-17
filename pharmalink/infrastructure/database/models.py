from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pharmalink.domain.enums import (
    FulfillmentType,
    OrderStatus,
    PaymentStatus,
    ReservationStatus,
    UserRole,
)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(unique=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.customer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Admin(Base, TimestampMixin):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped[User] = relationship()


class Pharmacy(Base, TimestampMixin):
    __tablename__ = "pharmacies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    legal_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)


class Branch(Base, TimestampMixin):
    __tablename__ = "branches"
    id: Mapped[int] = mapped_column(primary_key=True)
    pharmacy_id: Mapped[int] = mapped_column(ForeignKey("pharmacies.id"))
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(32))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    is_active: Mapped[bool] = mapped_column(default=True)
    pharmacy: Mapped[Pharmacy] = relationship()


class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)


class Manufacturer(Base, TimestampMixin):
    __tablename__ = "manufacturers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    country: Mapped[str | None] = mapped_column(String(128))


class Medicine(Base, TimestampMixin):
    __tablename__ = "medicines"
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    manufacturer_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturers.id"))
    name: Mapped[str] = mapped_column(String(255), index=True)
    barcode: Mapped[str | None] = mapped_column(String(128), unique=True)
    active_ingredient: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    dosage: Mapped[str | None] = mapped_column(String(128))
    prescription_required: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    category: Mapped[Category | None] = relationship()
    manufacturer: Mapped[Manufacturer | None] = relationship()


class Inventory(Base, TimestampMixin):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("branch_id", "medicine_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    branch: Mapped[Branch] = relationship()
    medicine: Mapped[Medicine] = relationship()


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    label: Mapped[str] = mapped_column(String(64))
    address: Mapped[str] = mapped_column(Text)
    user: Mapped[User] = relationship()


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    fulfillment_type: Mapped[FulfillmentType] = mapped_column(Enum(FulfillmentType))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    items: Mapped[list["OrderItem"]] = relationship(cascade="all, delete-orphan")


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    medicine: Mapped[Medicine] = relationship()


class Reservation(Base, TimestampMixin):
    __tablename__ = "reservations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus), default=ReservationStatus.active
    )
    expires_at: Mapped[datetime]


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    provider: Mapped[str] = mapped_column(String(64))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.pending
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    external_id: Mapped[str | None] = mapped_column(String(255))


class Coupon(Base, TimestampMixin):
    __tablename__ = "coupons"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    discount_percent: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True)


class Favorite(Base, TimestampMixin):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "medicine_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id"))


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(default=False)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(128))
    entity: Mapped[str] = mapped_column(String(128))
    entity_id: Mapped[str] = mapped_column(String(128))
    payload: Mapped[str | None] = mapped_column(Text)


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    position: Mapped[str] = mapped_column(String(128))
    user: Mapped[User] = relationship()
    branch: Mapped[Branch] = relationship()


Index("ix_medicine_search", Medicine.name, Medicine.barcode, Medicine.active_ingredient)
