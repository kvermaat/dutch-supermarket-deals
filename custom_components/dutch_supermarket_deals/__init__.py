"""Dutch Supermarket Deals integration."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)
from homeassistant.helpers.storage import Store

from .api import (
    PrijsProfeetClient,
    PrijsProfeetConnectionError,
    PrijsProfeetResponseError,
)
from .const import DEFAULT_LIMIT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.settings"


class DutchSupermarketStorage:
    """Store shared supermarket-card settings."""

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize persistent storage."""
        self._store: Store[
            dict[str, Any]
        ] = Store(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY,
        )

        self._data: dict[str, Any] = {
            "lists": {},
        }

        self._lock = asyncio.Lock()

    async def async_load(self) -> None:
        """Load stored settings."""
        stored = await self._store.async_load()

        if not isinstance(stored, dict):
            self._data = {
                "lists": {},
            }
            return

        lists = stored.get("lists")

        if not isinstance(lists, dict):
            lists = {}

        self._data = {
            "lists": lists,
        }

    async def async_get_list(
        self,
        list_id: str,
    ) -> dict[str, Any]:
        """Return one shared product list."""
        async with self._lock:
            lists = self._data.setdefault(
                "lists",
                {},
            )

            stored = lists.get(list_id)

            if not isinstance(stored, dict):
                return default_list_settings()

            return normalize_settings(stored)

    async def async_save_list(
        self,
        list_id: str,
        settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Save one shared product list."""
        normalized = normalize_settings(
            settings
        )

        async with self._lock:
            lists = self._data.setdefault(
                "lists",
                {},
            )

            lists[list_id] = normalized

            await self._store.async_save(
                self._data
            )

        return normalized


async def async_setup(
    hass: HomeAssistant,
    config: dict[str, Any],
) -> bool:
    """Set up Dutch Supermarket Deals."""
    hass.data.setdefault(DOMAIN, {})

    storage = DutchSupermarketStorage(hass)
    await storage.async_load()

    hass.data[DOMAIN]["storage"] = storage

    websocket_api.async_register_command(
        hass,
        websocket_get_settings,
    )

    websocket_api.async_register_command(
        hass,
        websocket_save_settings,
    )

    websocket_api.async_register_command(
        hass,
        websocket_search,
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up the integration entry."""
    session = async_get_clientsession(hass)

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        "client": PrijsProfeetClient(
            session
        ),
    }

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload the integration entry."""
    hass.data.get(
        DOMAIN,
        {},
    ).pop(
        entry.entry_id,
        None,
    )

    return True


@websocket_api.websocket_command(
    {
        vol.Required("type"):
            f"{DOMAIN}/get_settings",

        vol.Optional(
            "list_id",
            default="default",
        ): vol.All(
            str,
            vol.Length(
                min=1,
                max=100,
            ),
        ),
    }
)
@websocket_api.async_response
async def websocket_get_settings(
    hass: HomeAssistant,
    connection:
        websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return settings shared across devices."""
    storage = get_storage(hass)

    settings = await storage.async_get_list(
        clean_list_id(
            msg["list_id"]
        )
    )

    connection.send_result(
        msg["id"],
        settings,
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"):
            f"{DOMAIN}/save_settings",

        vol.Optional(
            "list_id",
            default="default",
        ): vol.All(
            str,
            vol.Length(
                min=1,
                max=100,
            ),
        ),

        vol.Required(
            "products"
        ): list,

        vol.Required(
            "retailers"
        ): list,

        vol.Required(
            "minimum_discount"
        ): vol.Coerce(float),
    }
)
@websocket_api.async_response
async def websocket_save_settings(
    hass: HomeAssistant,
    connection:
        websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save settings shared across devices."""
    try:
        settings = normalize_settings(
            {
                "products":
                    msg["products"],

                "retailers":
                    msg["retailers"],

                "minimum_discount":
                    msg["minimum_discount"],
            }
        )

    except ValueError as err:
        connection.send_error(
            msg["id"],
            "invalid_settings",
            str(err),
        )
        return

    storage = get_storage(hass)

    saved = await storage.async_save_list(
        clean_list_id(
            msg["list_id"]
        ),
        settings,
    )

    connection.send_result(
        msg["id"],
        saved,
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"):
            f"{DOMAIN}/search",

        vol.Required(
            "query"
        ): str,

        vol.Optional(
            "category",
            default="",
        ): str,

        vol.Optional(
            "exclude_words",
            default=[],
        ): list,

        vol.Optional(
            "retailers",
            default=[],
        ): list,

        vol.Optional(
            "minimum_discount",
            default=0,
        ): vol.Coerce(float),

        vol.Optional(
            "limit",
            default=DEFAULT_LIMIT,
        ): vol.All(
            vol.Coerce(int),
            vol.Range(
                min=1,
                max=100,
            ),
        ),

        vol.Optional(
            "current_only",
            default=True,
        ): bool,
    }
)
@websocket_api.async_response
async def websocket_search(
    hass: HomeAssistant,
    connection:
        websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Search for supermarket products."""
    entries = (
        hass.config_entries.async_entries(
            DOMAIN
        )
    )

    if not entries:
        connection.send_error(
            msg["id"],
            "not_configured",
            (
                "Dutch Supermarket Deals "
                "is not configured"
            ),
        )
        return

    entry = entries[0]

    integration_data = hass.data.get(
        DOMAIN,
        {},
    ).get(entry.entry_id)

    if integration_data is None:
        connection.send_error(
            msg["id"],
            "not_loaded",
            (
                "Dutch Supermarket Deals "
                "is not loaded"
            ),
        )
        return

    client: PrijsProfeetClient = (
        integration_data["client"]
    )

    try:
        raw_results = await client.async_search(
            query=msg["query"],
            limit=msg["limit"],
        )

    except PrijsProfeetConnectionError as err:
        _LOGGER.warning(
            "PrijsProfeet connection error: %s",
            err,
        )

        connection.send_error(
            msg["id"],
            "connection_error",
            str(err),
        )
        return

    except PrijsProfeetResponseError as err:
        _LOGGER.warning(
            "PrijsProfeet response error: %s",
            err,
        )

        connection.send_error(
            msg["id"],
            "invalid_response",
            str(err),
        )
        return
    selected_retailers = {
        clean_retailer(retailer)
        for retailer in msg["retailers"]
        if isinstance(retailer, str)
        and retailer.strip()
    }

    selected_category = clean_category(
        msg.get("category")
    )

    exclude_words = normalize_exclude_words(
        msg.get(
            "exclude_words",
            [],
        )
    )

    minimum_discount = max(
        0.0,
        min(
            100.0,
            float(
                msg["minimum_discount"]
            ),
        ),
    )

    current_only = bool(
        msg["current_only"]
    )

    results: list[
        dict[str, Any]
    ] = []

    for item in raw_results:
        if not isinstance(
            item,
            dict,
        ):
            continue

        normalized = normalize_product(
            item
        )

        retailer = clean_retailer(
            normalized["retailer"]
        )

        category = clean_category(
            normalized["category"]
        )

        product_name = str(
            normalized["name"]
        ).casefold()

        if (
            selected_retailers
            and retailer
            not in selected_retailers
        ):
            continue

        if (
            selected_category
            and category
            != selected_category
        ):
            continue

        if any(
            excluded.casefold()
            in product_name
            for excluded
            in exclude_words
        ):
            continue

        if (
            normalized["discount"]
            < minimum_discount
        ):
            continue

        if (
            current_only
            and not normalized[
                "is_current_deal"
            ]
        ):
            continue

        results.append(
            normalized
        )

    results.sort(
        key=lambda product: (
            -product["discount"],
            product["price"],
        )
    )

    connection.send_result(
        msg["id"],
        {
            "query":
                msg["query"],

            "category":
                selected_category,

            "exclude_words":
                exclude_words,

            "count":
                len(results),

            "results":
                results,
        },
    )


def get_storage(
    hass: HomeAssistant,
) -> DutchSupermarketStorage:
    """Return integration storage."""
    storage = hass.data.get(
        DOMAIN,
        {},
    ).get("storage")

    if not isinstance(
        storage,
        DutchSupermarketStorage,
    ):
        raise RuntimeError(
            (
                "Dutch Supermarket Deals "
                "storage is unavailable"
            )
        )

    return storage


def default_list_settings(
) -> dict[str, Any]:
    """Return default shared settings."""
    return {
        "products": [],

        "retailers": [
            "albert-heijn",
            "jumbo",
            "plus",
            "dirk",
        ],

        "minimum_discount":
            20,
    }


def normalize_settings(
    settings: dict[str, Any],
) -> dict[str, Any]:
    """Validate and normalize settings."""
    raw_products = settings.get(
        "products",
        [],
    )

    if not isinstance(
        raw_products,
        list,
    ):
        raise ValueError(
            "Products must be a list"
        )

    if len(raw_products) > 100:
        raise ValueError(
            (
                "A maximum of 100 watched "
                "products is supported"
            )
        )

    products: list[
        dict[str, Any]
    ] = []

    seen_products: set[
        tuple[
            str,
            str,
            tuple[str, ...],
        ]
    ] = set()

    for raw_product in raw_products:
        if not isinstance(
            raw_product,
            dict,
        ):
            continue

        query = str(
            raw_product.get(
                "query",
                "",
            )
        ).strip().strip(
            "\"'"
        )

        if not query:
            continue

        if len(query) > 200:
            query = query[:200]

        category = clean_category(
            raw_product.get(
                "category",
                "",
            )
        )

        exclude_words = (
            normalize_exclude_words(
                raw_product.get(
                    "exclude_words",
                    raw_product.get(
                        "excludeWords",
                        [],
                    ),
                )
            )
        )

        duplicate_key = (
            query.casefold(),
            category,
            tuple(
                word.casefold()
                for word
                in exclude_words
            ),
        )

        if duplicate_key in seen_products:
            continue

        seen_products.add(
            duplicate_key
        )

        minimum_discount = to_float(
            raw_product.get(
                "minimumDiscount",
                raw_product.get(
                    "minimum_discount",
                    settings.get(
                        "minimum_discount",
                        20,
                    ),
                ),
            )
        )

        minimum_discount = max(
            0.0,
            min(
                100.0,
                minimum_discount,
            ),
        )

        product: dict[
            str,
            Any,
        ] = {
            "query":
                query,

            "minimumDiscount":
                minimum_discount,

            "category":
                category,

            "exclude_words":
                exclude_words,
        }

        product_retailers = (
            raw_product.get(
                "retailers"
            )
        )

        if isinstance(
            product_retailers,
            list,
        ):
            product["retailers"] = (
                normalize_retailers(
                    product_retailers
                )
            )

        products.append(
            product
        )

    retailers = normalize_retailers(
        settings.get(
            "retailers",
            [],
        )
    )

    minimum_discount = max(
        0.0,
        min(
            100.0,
            to_float(
                settings.get(
                    "minimum_discount",
                    20,
                )
            ),
        ),
    )

    return {
        "products":
            products,

        "retailers":
            retailers,

        "minimum_discount":
            minimum_discount,
    }


def normalize_retailers(
    values: Any,
) -> list[str]:
    """Normalize a retailer list."""
    if not isinstance(
        values,
        list,
    ):
        return []

    result: list[str] = []

    for value in values:
        if not isinstance(
            value,
            str,
        ):
            continue

        retailer = clean_retailer(
            value
        )

        if (
            retailer
            and retailer not in result
        ):
            result.append(
                retailer
            )

    return result


def normalize_exclude_words(
    values: Any,
) -> list[str]:
    """Normalize excluded words and phrases."""
    if isinstance(
        values,
        str,
    ):
        values = re.split(
            r"[,;\n]+",
            values,
        )

    if not isinstance(
        values,
        list,
    ):
        return []

    result: list[str] = []

    for value in values:
        if not isinstance(
            value,
            str,
        ):
            continue

        word = " ".join(
            value.strip().split()
        )

        if not word:
            continue

        if len(word) > 100:
            word = word[:100]

        existing_words = {
            item.casefold()
            for item in result
        }

        if (
            word.casefold()
            not in existing_words
        ):
            result.append(
                word
            )

        if len(result) >= 30:
            break

    return result
def clean_list_id(
    value: str,
) -> str:
    """Normalize the shared-list ID."""
    cleaned = str(
        value
    ).strip()

    return (
        cleaned
        or "default"
    )


def clean_retailer(
    value: Any,
) -> str:
    """Normalize retailer slugs.

    PrijsProfeet may return retailer names
    such as "albert_heijn", while the card
    uses "albert-heijn".

    All common separators are normalized
    to a hyphen so both values match.
    """
    retailer = str(
        value or ""
    ).strip().lower()

    retailer = retailer.replace(
        "&",
        "and",
    )

    retailer = re.sub(
        r"[\s_]+",
        "-",
        retailer,
    )

    retailer = re.sub(
        r"-+",
        "-",
        retailer,
    )

    retailer = retailer.strip(
        "-"
    )

    aliases = {
        "ah":
            "albert-heijn",

        "albertheijn":
            "albert-heijn",

        "albert-heijn":
            "albert-heijn",

        "albert-heijn-nl":
            "albert-heijn",
    }

    return aliases.get(
        retailer,
        retailer,
    )


def clean_category(
    value: Any,
) -> str:
    """Normalize a category slug."""
    category = str(
        value or ""
    ).strip().lower()

    category = category.replace(
        "&",
        " ",
    )

    category = re.sub(
        r"[^a-z0-9]+",
        "-",
        category,
    )

    return category.strip(
        "-"
    )


def normalize_product(
    item: dict[str, Any],
) -> dict[str, Any]:
    """Normalize a PrijsProfeet product."""
    price = to_float(
        first_value(
            item,
            "price",
            "current_price",
            "offer_price",
        )
    )

    original_price = to_float(
        first_value(
            item,
            "original_price",
            "regular_price",
            "was_price",
        )
    )

    supplied_discount = to_float(
        first_value(
            item,
            "savings_percentage",
            "discount_percentage",
            "discount_percent",
            "discount",
        )
    )

    calculated_discount = 0.0

    if (
        original_price > 0
        and original_price > price
    ):
        calculated_discount = (
            (
                original_price
                - price
            )
            / original_price
            * 100
        )

    discount = round(
        supplied_discount
        or calculated_discount,
        2,
    )

    promotion_status = str(
        item.get(
            "promotion_status",
            "",
        )
    ).lower()

    is_current_deal = bool(
        item.get(
            "is_current_deal",
            item.get(
                "active",
                promotion_status
                in (
                    "",
                    "active",
                    "current",
                ),
            ),
        )
    )

    category = clean_category(
        first_value(
            item,
            "unified_category",
            "category",
            "category_slug",
            "category_name",
        )
    )

    retailer = clean_retailer(
        first_value(
            item,
            "retailer",
            "retailer_slug",
            "store",
            "supermarket",
        )
    )

    return {
        "id":
            first_value(
                item,
                "id",
                "product_id",
                "ean",
            ),

        "ean":
            item.get(
                "ean"
            ),

        "name":
            (
                first_value(
                    item,
                    "name",
                    "title",
                    "product_name",
                )
                or "Unknown product"
            ),

        "retailer":
            retailer or "unknown",

        "category":
            category,

        "price":
            price,

        "original_price":
            original_price,

        "discount":
            discount,

        "is_promotional":
            bool(
                item.get(
                    "is_promotional",
                    discount > 0,
                )
            ),

        "is_current_deal":
            is_current_deal,

        "promotion_status":
            promotion_status,

        "valid_from":
            first_value(
                item,
                "valid_from",
                "start_date",
            ),

        "valid_until":
            first_value(
                item,
                "valid_until",
                "end_date",
            ),

        "image":
            first_value(
                item,
                "image",
                "image_url",
                "thumbnail",
            ),

        "url":
            first_value(
                item,
                "url",
                "product_url",
                "link",
            ),
    }


def first_value(
    item: dict[str, Any],
    *keys: str,
) -> Any:
    """Return the first populated value."""
    for key in keys:
        value = item.get(
            key
        )

        if (
            value is not None
            and value != ""
        ):
            return value

    return None


def to_float(
    value: Any,
) -> float:
    """Convert an API value to float."""
    try:
        return float(
            value or 0
        )

    except (
        TypeError,
        ValueError,
    ):
        return 0.0
