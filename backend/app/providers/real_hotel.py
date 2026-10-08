# app/providers/real_hotel.py
"""Real hotel provider (MakCorps). Fails loudly: it never invents hotels."""
import logging
import re
from decimal import Decimal, InvalidOperation

import httpx

from app.core.config import settings
from app.schemas.tools import HotelSearchInput
from app.schemas.travel import Hotel

logger = logging.getLogger(__name__)

# UNVERIFIED: this URL/param shape returned 404 before. Confirm against the
# official docs in your MakCorps account (https://www.makcorps.com/documentation/).
MAKCORPS_BASE_URL = "https://api.makcorps.com/free"

_SYMBOLS = {"US$": "USD", "$": "USD", "€": "EUR", "£": "GBP", "₹": "INR", "¥": "JPY"}


class MakCorpsError(Exception):
    """Raised when the MakCorps call fails or returns something we can't use."""


def _parse_price(raw: object) -> tuple[Decimal, str] | None:
    """'US$205' -> (Decimal('205'), 'USD'). Returns None if there is no usable price."""
    if not raw or not isinstance(raw, str):
        return None
    digits = re.sub(r"[^\d.]", "", raw)
    if not digits:
        return None
    currency = next((code for sym, code in _SYMBOLS.items() if sym in raw), None)
    if currency is None:
        return None  # unknown currency: we never guess
    try:
        return Decimal(digits), currency
    except InvalidOperation:
        return None


class RealHotelProvider:
    def __init__(self, timeout: float = 15.0):
        self._timeout = timeout

    async def search(self, input: HotelSearchInput) -> list[Hotel]:
        if not settings.makcorps_rapidapi_key:
            raise MakCorpsError("MakCorps API key is not configured")

        nights = max(1, (input.check_out - input.check_in).days)
        params = {
            "city": input.city,
            "checkin": input.check_in.isoformat(),
            "checkout": input.check_out.isoformat(),
            "rooms": 1,
            "adults": input.guests,
            "currency": input.currency,
            "api_key": settings.makcorps_rapidapi_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(MAKCORPS_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            logger.error("MakCorps request failed: %s status=%s", type(exc).__name__, status)
            raise MakCorpsError(
                f"hotel request failed: {type(exc).__name__} status={status}"
            ) from None
        entries = data.get("hotels") if isinstance(data, dict) else data
        if not isinstance(entries, list) or not entries:
            raise MakCorpsError("unexpected or empty response shape")

        hotels: list[Hotel] = []
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            name = entry.get("Hotel") or entry.get("name")
            quotes = [
                _parse_price(entry.get(f"vendor{n}-price")) for n in (1, 2, 3)
            ]
            quotes = [q for q in quotes if q is not None]
            if not name or not quotes:
                continue  # skip entries we can't trust; do not invent a price
            price, currency = min(quotes, key=lambda q: q[0])
            # ASSUMPTION: quoted price is per night. Verify against the docs.
            hotels.append(
                Hotel(
                    id=f"makcorps-{i + 1}",
                    name=name,
                    city=input.city,
                    price_per_night=price,
                    nights=nights,
                    currency=currency,
                )
            )

        if not hotels:
            raise MakCorpsError("no hotels with a usable price in the response")
        return hotels