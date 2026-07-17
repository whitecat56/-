from typing import Any

import httpx

from pharmalink.config.settings import Settings
from pharmalink.infrastructure.integrations.base import BaseERPAdapter


class CustomERPAdapter(BaseERPAdapter):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def _request(self, method: str, path: str, json: dict[str, Any] | None = None):
        async with httpx.AsyncClient(base_url=self.settings.erp_url, timeout=20) as client:
            return (
                await client.request(
                    method,
                    path,
                    json=json,
                    auth=(
                        (self.settings.erp_login, self.settings.erp_password)
                        if self.settings.erp_login
                        else None
                    ),
                )
            ).json()

    async def sync_products(self):
        return await self._request("GET", "/products")

    async def sync_inventory(self):
        return await self._request("GET", "/inventory")

    async def create_order(self, order):
        return await self._request("POST", "/orders", order)

    async def reserve_order(self, order):
        return await self._request("POST", "/reservations", order)

    async def cancel_order(self, external_id):
        return await self._request("POST", f"/orders/{external_id}/cancel")
