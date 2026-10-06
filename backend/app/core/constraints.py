from decimal import Decimal

from app.schemas import Hotel, ConstraintResult, ConstraintViolation


class ConstraintEngine:
    """
    Checks a fixed set of hard constraints. Deterministic — every
    check here is a plain comparison, never an LLM judgment call.

    Extend this by adding a new `_check_*` method and calling it
    from `check()`. Do not add a plugin/registry system for this
    until we actually have enough constraint types to justify one.
    """

    def check(
        self,
        *,
        total_cost: Decimal,
        budget: Decimal,
        hotels: list[Hotel],
        max_hotel_price_per_night: Decimal | None = None,
        travellers: int,
        expected_travellers: int,
        duration_days: int,
        expected_duration_days: int,
    ) -> ConstraintResult:
        violations: list[ConstraintViolation] = []

        if total_cost > budget:
            violations.append(
                ConstraintViolation(
                    constraint="budget",
                    expected=str(budget),
                    actual=str(total_cost),
                )
            )

        if max_hotel_price_per_night is not None:
            for hotel in hotels:
                if hotel.price_per_night > max_hotel_price_per_night:
                    violations.append(
                        ConstraintViolation(
                            constraint=f"hotel_price:{hotel.id}",
                            expected=str(max_hotel_price_per_night),
                            actual=str(hotel.price_per_night),
                        )
                    )

        if travellers != expected_travellers:
            violations.append(
                ConstraintViolation(
                    constraint="travellers",
                    expected=str(expected_travellers),
                    actual=str(travellers),
                )
            )

        if duration_days != expected_duration_days:
            violations.append(
                ConstraintViolation(
                    constraint="duration_days",
                    expected=str(expected_duration_days),
                    actual=str(duration_days),
                )
            )

        return ConstraintResult(passed=len(violations) == 0, violations=violations)