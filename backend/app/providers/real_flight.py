from decimal import Decimal

import httpx

from app.core.config import settings
from app.schemas.tools import FlightSearchInput
from app.schemas.travel import Flight

DUFFEL_BASE_URL = "https://api.duffel.com"
DUFFEL_VERSION = "v2"


class DuffelError(Exception):
    """Raised when Duffel can't be reached or returns something unusable."""


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.duffel_api_key}",
        "Duffel-Version": DUFFEL_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


class RealFlightProvider:
    """
    Test vs. live mode is decided by which token you put in settings
    (duffel_test_... vs duffel_live_...), not by the URL — unlike
    every other real provider in this project so far.
    """

    def __init__(self, timeout: float = 20.0):
        self._timeout = timeout

    async def search(self, input: FlightSearchInput) -> list[Flight]:
        origin_code = await self._resolve_airport(input.origin)
        destination_code = await self._resolve_airport(input.destination)

        body = {
            "data": {
                "cabin_class": "economy",
                "slices": [{
                    "origin": origin_code,
                    "destination": destination_code,
                    "departure_date": input.departure_date.isoformat(),
                }],
                "passengers": [{"type": "adult"} for _ in range(input.travellers)],
            }
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(
                    f"{DUFFEL_BASE_URL}/air/offer_requests", headers=_headers(), json=body,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise DuffelError(f"flight search failed: {exc}") from exc

        offers = response.json().get("data", {}).get("offers", [])
        if not offers:
            raise DuffelError(
                f"no flights found for {input.origin} -> {input.destination} on "
                f"{input.departure_date} — confirm your token has a duffel_test_ "
                f"prefix and try a well-covered route"
            )

        flights = []
        for offer in offers[:5]:
            airline = offer.get("owner", {}).get("name", "Unknown")
            flights.append(Flight(
                id=offer["id"], airline=airline,
                price=Decimal(offer["total_amount"]), currency=offer["total_currency"],
            ))
        return flights

    async def _resolve_airport(self, keyword: str) -> str:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{DUFFEL_BASE_URL}/places/suggestions",
                    headers=_headers(), params={"query": keyword},
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise DuffelError(f"airport lookup failed for '{keyword}': {exc}") from exc

        results = response.json().get("data", [])
        if not results:
            raise DuffelError(f"no airport found for '{keyword}'")

        return results[0]["iata_code"]