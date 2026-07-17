import asyncio

import structlog

from pharmalink.config.settings import get_settings
from pharmalink.infrastructure.integrations.factory import build_adapter

log = structlog.get_logger()


async def run_sync_forever():
    settings = get_settings()
    adapter = build_adapter(settings)
    while True:
        if settings.erp_enabled:
            products = await adapter.sync_products()
            inventory = await adapter.sync_inventory()
            log.info("erp_sync_completed", products=len(products), inventory=len(inventory))
        await asyncio.sleep(settings.sync_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_sync_forever())
