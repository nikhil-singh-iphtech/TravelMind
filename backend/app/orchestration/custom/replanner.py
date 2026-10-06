import logging
from decimal import Decimal

from app.schemas.state import TravelState

logger = logging.getLogger(__name__)

MAX_REPLANS = 3

# Each retry shrinks the hotel price ceiling further, on top of switching
# to the cheapest-option strategy. Both are plain, explainable rules.
HOTEL_CAP_SHRINK_FACTOR = Decimal("0.8")


class Replanner:
    """
    Deterministic. Decides what to change before the next attempt —
    never asks an LLM what to try, per the project's own rule that
    Python, not the model, drives replanning decisions.
    """

    def should_replan(self, state: TravelState) -> bool:
        return state.constraint_result is not None and not state.constraint_result.passed and state.iteration < MAX_REPLANS

    def replan(self, state: TravelState) -> None:
        state.iteration += 1

        # Rule 1: a "comfort" plan that's over budget switches to picking
        # the cheapest candidates instead of the priciest.
        if state.strategy == "comfort":
            state.strategy = "budget"
            reason = "switched selection strategy from comfort to budget"
        else:
            # Rule 2: already on "budget" and still over -> tighten the
            # hotel price ceiling so the next search returns cheaper hotels.
            current_cap = state.request.max_hotel_price_per_night
            if current_cap is None:
                # No explicit cap set yet — derive one from the hotel we
                # actually selected, then shrink it.
                current_cap = state.selected_hotel.price_per_night if state.selected_hotel else Decimal("10000")
            state.request.max_hotel_price_per_night = (current_cap * HOTEL_CAP_SHRINK_FACTOR).quantize(Decimal("1"))
            reason = f"tightened hotel price cap to {state.request.max_hotel_price_per_night}"

        logger.info("run=%s iteration=%d replan: %s", state.run_id, state.iteration, reason)
        state.events.append(
            state.events[0].__class__(  # WorkflowEvent, avoids a circular import here
                run_id=state.run_id,
                event_type="replanning_started",
                message=f"Attempt {state.iteration}: {reason}",
            )
        )