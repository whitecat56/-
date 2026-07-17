from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from pharmalink.domain.enums import FulfillmentType, OrderStatus, UserRole


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr | None = None
    phone: str | None = None
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    full_name: str
    email: str | None
    phone: str | None
    role: UserRole


class MedicineRead(BaseModel):
    id: int
    name: str
    barcode: str | None = None
    active_ingredient: str | None = None
    description: str | None = None
    dosage: str | None = None
    prescription_required: bool


class MedicineCreate(BaseModel):
    name: str
    barcode: str | None = None
    active_ingredient: str | None = None
    description: str | None = None
    dosage: str | None = None
    category_id: int | None = None
    manufacturer_id: int | None = None
    prescription_required: bool = False


class InventoryRead(BaseModel):
    branch_id: int
    medicine_id: int
    quantity: int
    reserved_quantity: int
    price: Decimal


class CartItem(BaseModel):
    medicine_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    branch_id: int
    fulfillment_type: FulfillmentType
    items: list[CartItem]


class OrderRead(BaseModel):
    id: int
    status: OrderStatus
    total_amount: Decimal
