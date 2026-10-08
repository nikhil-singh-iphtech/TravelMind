from decimal import Decimal
from app.core.budget import BudgetCalculator
from app.core.currency import convert
from app.orchestration.rules import FOOD_PER_PERSON_PER_DAY, TRANSPORT_PER_PERSON_PER_DAY
from app.schemas import Flight, Hotel, Activity
from app.schemas.budget_advice import BudgetAdvice, BudgetSuggestion
from app.schemas.state import TravelRequest, TravelState


class BudgetAdvisor:
    """
    Deterministic Python engine that evaluates failed or sub-optimal trip plans and computes
    actionable, ranked recommendations (swapping flight, hotel, dropping activities, or increasing budget).
    """

    def analyze(self, request: TravelRequest, state: TravelState) -> BudgetAdvice:
        budget = request.budget
        target_currency = request.currency
        days, n = request.duration_days, request.travellers

        # Calculate fixed transport and food costs converted to budget currency
        transport_cost = TRANSPORT_PER_PERSON_PER_DAY * n * days
        food_cost = FOOD_PER_PERSON_PER_DAY * n * days

        # Find absolute cheapest flight option
        all_flights = state.flights or ([state.selected_flight] if state.selected_flight else [])
        cheapest_flight = min(all_flights, key=lambda f: convert(f.price, f.currency, target_currency)) if all_flights else state.selected_flight

        # Find absolute cheapest hotel option
        all_hotels = state.hotels or ([state.selected_hotel] if state.selected_hotel else [])
        cheapest_hotel = min(
            all_hotels,
            key=lambda h: convert(h.price_per_night * h.nights, h.currency, target_currency)
        ) if all_hotels else state.selected_hotel

        # Calculate minimum possible total cost
        cheapest_flight_cost = convert(cheapest_flight.price, cheapest_flight.currency, target_currency) if cheapest_flight else Decimal("0")
        cheapest_hotel_cost = convert(cheapest_hotel.price_per_night * cheapest_hotel.nights, cheapest_hotel.currency, target_currency) if cheapest_hotel else Decimal("0")
        cheapest_activities_cost = Decimal("0") # optional activities dropped in minimum case

        cheapest_possible_total = (
            cheapest_flight_cost
            + cheapest_hotel_cost
            + cheapest_activities_cost
            + transport_cost
            + food_cost
        )

        current_total = state.budget_result.total if state.budget_result else cheapest_possible_total

        # Scenario 1: Plan is already within budget
        if current_total <= budget:
            return BudgetAdvice(
                status="within_budget",
                gap=budget - current_total,
                cheapest_possible_total=cheapest_possible_total,
                recommended_budget=budget,
                suggestions=[],
            )

        # Scenario 2: Plan is reducible (cheapest possible total fits within budget)
        if cheapest_possible_total <= budget:
            suggestions: list[BudgetSuggestion] = []

            # Check if swapping flight helps
            if state.selected_flight and cheapest_flight and state.selected_flight.id != cheapest_flight.id:
                cur_f_cost = convert(state.selected_flight.price, state.selected_flight.currency, target_currency)
                saving = cur_f_cost - cheapest_flight_cost
                if saving > 0:
                    suggestions.append(
                        BudgetSuggestion(
                            component="flight",
                            action=f"Switch to cheaper airline option ({cheapest_flight.airline})",
                            estimated_saving=saving,
                            resulting_total=current_total - saving,
                        )
                    )

            # Check if swapping hotel helps
            if state.selected_hotel and cheapest_hotel and state.selected_hotel.id != cheapest_hotel.id:
                cur_h_cost = convert(state.selected_hotel.price_per_night * state.selected_hotel.nights, state.selected_hotel.currency, target_currency)
                saving = cur_h_cost - cheapest_hotel_cost
                if saving > 0:
                    suggestions.append(
                        BudgetSuggestion(
                            component="hotel",
                            action=f"Choose budget-friendly hotel ({cheapest_hotel.name})",
                            estimated_saving=saving,
                            resulting_total=current_total - saving,
                        )
                    )

            # Check if trimming activities helps
            if state.activities:
                highest_activity = max(state.activities, key=lambda a: a.price)
                act_saving = convert(highest_activity.price, target_currency, target_currency)
                suggestions.append(
                    BudgetSuggestion(
                        component="activities",
                        action=f"Remove optional activity '{highest_activity.name}'",
                        estimated_saving=act_saving,
                        resulting_total=current_total - act_saving,
                    )
                )

            # Sort suggestions by smallest sacrifice / highest saving
            suggestions.sort(key=lambda s: s.estimated_saving, reverse=True)

            return BudgetAdvice(
                status="reducible",
                gap=current_total - budget,
                cheapest_possible_total=cheapest_possible_total,
                recommended_budget=cheapest_possible_total,
                suggestions=suggestions,
            )

        # Scenario 3: Increase needed (even absolute cheapest options exceed target budget)
        gap = cheapest_possible_total - budget
        recommended_buffer = Decimal("10000") # 10,000 unit safety buffer
        recommended_budget = cheapest_possible_total + recommended_buffer

        suggestions = [
            BudgetSuggestion(
                component="duration",
                action=f"Increase budget by at least {gap} {target_currency} to cover essential flights & stay",
                estimated_saving=Decimal("0"),
                resulting_total=cheapest_possible_total,
            )
        ]

        return BudgetAdvice(
            status="increase_needed",
            gap=gap,
            cheapest_possible_total=cheapest_possible_total,
            recommended_budget=recommended_budget,
            suggestions=suggestions,
        )
