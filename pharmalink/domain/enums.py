from enum import StrEnum


class UserRole(StrEnum):
    customer = "customer"
    employee = "employee"
    admin = "admin"


class OrderStatus(StrEnum):
    draft = "draft"
    pending = "pending"
    confirmed = "confirmed"
    ready = "ready"
    completed = "completed"
    canceled = "canceled"


class FulfillmentType(StrEnum):
    pickup = "pickup"
    delivery = "delivery"


class PaymentStatus(StrEnum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


class ReservationStatus(StrEnum):
    active = "active"
    fulfilled = "fulfilled"
    canceled = "canceled"
    expired = "expired"
