from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class BookingProviderResult:
    def __init__(self, available: bool, revalidated_price: Decimal, error_message: str | None = None):
        self.available = available
        self.revalidated_price = revalidated_price
        self.error_message = error_message


class MockBookingProvider:
    """
    Mock booking provider with configurable flags for testing edge cases
    (e.g., price changes, unavailability, or simulated failures).
    """

    def __init__(self, simulate_price_increase: bool = False, simulate_unavailability: bool = False):
        self.simulate_price_increase = simulate_price_increase
        self.simulate_unavailability = simulate_unavailability

    async def revalidate_and_reserve(
        self, flight_id: str | None, hotel_id: str | None, quoted_price: Decimal
    ) -> BookingProviderResult:
        if self.simulate_unavailability:
            return BookingProviderResult(
                available=False,
                revalidated_price=quoted_price,
                error_message="Selected flight/hotel offer is no longer available."
            )

        if self.simulate_price_increase:
            # Simulate a 10% price increase from provider
            new_price = (quoted_price * Decimal("1.10")).quantize(Decimal("0.01"))
            return BookingProviderResult(available=True, revalidated_price=new_price)

        return BookingProviderResult(available=True, revalidated_price=quoted_price)
