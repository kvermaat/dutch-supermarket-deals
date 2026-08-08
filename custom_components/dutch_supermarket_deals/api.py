"""PrijsProfeet API client."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientSession
from homeassistant.exceptions import HomeAssistantError

from .const import API_BASE_URL, DEFAULT_LIMIT, DEFAULT_TIMEOUT


class PrijsProfeetError(HomeAssistantError):
    """Base PrijsProfeet exception."""


class PrijsProfeetConnectionError(PrijsProfeetError):
    """Raised when PrijsProfeet cannot be reached."""


class PrijsProfeetResponseError(PrijsProfeetError):
    """Raised when PrijsProfeet returns an invalid response."""


class PrijsProfeetClient:
    """Small client for the PrijsProfeet API."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the client."""
        self._session = session

    async def async_search(
        self,
        query: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict[str, Any]]:
        """Search for supermarket products."""
        cleaned_query = query.strip().strip("\"'")

        if not cleaned_query:
            return []

        limit = max(1, min(limit, 100))

        url = f"{API_BASE_URL}/search"
        params = {
            "q": cleaned_query,
            "limit": limit,
        }

        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await self._session.get(
                    url,
                    params=params,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": (
                            "HomeAssistant-DutchSupermarketDeals/0.1"
                        ),
                    },
                )

                if response.status != 200:
                    body = await response.text()
                    raise PrijsProfeetResponseError(
                        f"PrijsProfeet returned HTTP {response.status}: "
                        f"{body[:200]}"
                    )

                payload = await response.json(content_type=None)

        except TimeoutError as err:
            raise PrijsProfeetConnectionError(
                "PrijsProfeet request timed out"
            ) from err

        except ClientError as err:
            raise PrijsProfeetConnectionError(
                f"Could not connect to PrijsProfeet: {err}"
            ) from err

        except ValueError as err:
            raise PrijsProfeetResponseError(
                "PrijsProfeet returned invalid JSON"
            ) from err

        if isinstance(payload, list):
            return payload

        if not isinstance(payload, dict):
            raise PrijsProfeetResponseError(
                "PrijsProfeet returned an unexpected response"
            )

        for key in ("results", "products", "items"):
            items = payload.get(key)

            if isinstance(items, list):
                return [
                    item
                    for item in items
                    if isinstance(item, dict)
                ]

        return []
