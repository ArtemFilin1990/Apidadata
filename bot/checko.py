from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CheckoClient:
    api_key: str
    base_url: str
    timeout_seconds: float
    _client: httpx.AsyncClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            headers={
                "Accept": "application/json",
                "X-API-KEY": self.api_key,
                "Authorization": f"Bearer {self.api_key}",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def find_party(self, inn: str) -> dict[str, Any] | None:
        for endpoint in ("/company", "/entrepreneur", "/person"):
            try:
                response = await self._client.get(endpoint, params={"inn": inn, "key": self.api_key})
            except httpx.HTTPError as exc:
                logger.warning("Checko transport error on %s: %s", endpoint, exc)
                continue

            if response.status_code == 404:
                continue
            if response.status_code >= 400:
                logger.warning("Checko status %s on %s: %s", response.status_code, endpoint, response.text)
                continue

            payload = response.json()
            normalized = _normalize_checko_payload(payload, inn)
            if normalized is not None:
                return normalized

        return None


def _normalize_checko_payload(payload: Any, inn: str) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    name = data.get("name") or data.get("full_name") or data.get("short_name") or f"ИНН {inn}"

    return {
        "value": str(name),
        "_source": "checko",
        "data": {
            "inn": str(data.get("inn") or inn),
            "ogrn": data.get("ogrn") or data.get("ogrnip"),
            "name": {
                "full_with_opf": data.get("full_name") or data.get("name"),
                "short_with_opf": data.get("short_name") or data.get("name"),
            },
            "state": {
                "status": data.get("status") or "ACTIVE",
                "registration_date": data.get("registration_date"),
                "liquidation_date": data.get("liquidation_date"),
            },
            "finance": {
                "year": data.get("finance_year"),
                "revenue": data.get("revenue"),
                "debt": data.get("tax_arrears"),
                "penalty": data.get("tax_penalties"),
            },
            "address": {
                "value": data.get("address"),
                "unrestricted_value": data.get("address"),
            },
            "management": {
                "name": data.get("director_name") or data.get("manager_name"),
                "post": data.get("director_post") or data.get("manager_post"),
            },
            "managers": [],
            "founders": [],
            "licenses": data.get("licenses") if isinstance(data.get("licenses"), list) else [],
            "phones": data.get("phones") if isinstance(data.get("phones"), list) else [],
            "emails": data.get("emails") if isinstance(data.get("emails"), list) else [],
        },
    }
