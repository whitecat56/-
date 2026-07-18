from enum import StrEnum


class LanguageCode(StrEnum):
    EN = "en"
    RU = "ru"
    UZ = "uz"


class Theme(StrEnum):
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"


class SubscriptionPlan(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class NotificationType(StrEnum):
    TRENDING = "trending"
    PREMIUM = "premium"
    SYSTEM = "system"
