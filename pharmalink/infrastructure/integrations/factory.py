from pharmalink.config.settings import Settings
from pharmalink.infrastructure.integrations.base import BaseERPAdapter
from pharmalink.infrastructure.integrations.custom import CustomERPAdapter
from pharmalink.infrastructure.integrations.mira import MiraERPAdapter
from pharmalink.infrastructure.integrations.one_c import OneCAdapter


def build_adapter(settings: Settings) -> BaseERPAdapter:
    return {
        "one_c": OneCAdapter,
        "1c": OneCAdapter,
        "mira": MiraERPAdapter,
        "custom": CustomERPAdapter,
        "mock": CustomERPAdapter,
    }.get(settings.erp_provider, CustomERPAdapter)(settings)
