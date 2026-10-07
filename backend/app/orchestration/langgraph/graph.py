from langgraph.graph import END, START, StateGraph

from app.services.memory_service import MemoryService

from app.embeddings.local_provider import SentenceTransformerProvider
from app.services.retriever_service import RetrieverService


from app.agents import ActivityAgent, BudgetAgent, ConstraintAgent, FlightAgent, HotelAgent, WeatherAgent
from app.llm.base import LLMProvider
from app.orchestration.langgraph.nodes import (
    _activity_input, _flight_input, _hotel_input, _weather_input,
    fail_node, finish_node, make_budget_node, make_constraint_node,
    replan_node, route_after_constraints, route_after_select, select_node, start_node,
    make_research_node,
)
from app.orchestration.langgraph.state import GraphState
from app.schemas.state import TravelRequest, TravelState


def build_graph(*, flight_agent, hotel_agent, activity_agent, weather_agent, budget_agent, constraint_agent):
    builder = StateGraph(GraphState)

    builder.add_node("start", start_node)
    builder.add_node("flight", make_research_node("flight", flight_agent, _flight_input, lambda d: {"flights": d.flights}))
    builder.add_node("hotel", make_research_node("hotel", hotel_agent, _hotel_input, lambda d: {"hotels": d.selected_hotels}))
    builder.add_node("activity", make_research_node("activity", activity_agent, _activity_input, lambda d: {"activities": d.activities}))
    builder.add_node("weather", make_research_node("weather", weather_agent, _weather_input, lambda d: {"weather": d.weather}))
    builder.add_node("select", select_node)
    builder.add_node("budget", make_budget_node(budget_agent))
    builder.add_node("constraint", make_constraint_node(constraint_agent))
    builder.add_node("replan", replan_node)
    builder.add_node("finish", finish_node)
    builder.add_node("fail", fail_node)

    builder.add_edge(START, "start")

    # Fan-out: start -> all four research nodes run concurrently.
    # Fan-in: all four -> select, which only fires once all four finish.
    for name in ["flight", "hotel", "activity", "weather"]:
        builder.add_edge("start", name)
        builder.add_edge(name, "select")

    builder.add_conditional_edges("select", route_after_select, {"fail": "fail", "budget": "budget"})
    builder.add_edge("budget", "constraint")
    builder.add_conditional_edges(
        "constraint", route_after_constraints, {"finish": "finish", "replan": "replan", "fail": "fail"}
    )

    # The cycle: replan goes back to the same four research nodes.
    for name in ["flight", "hotel", "activity", "weather"]:
        builder.add_edge("replan", name)

    builder.add_edge("finish", END)
    builder.add_edge("fail", END)

    return builder.compile()


def build_graph_from_llm(llm: LLMProvider):
    return build_graph(
        flight_agent=FlightAgent(llm),
        hotel_agent=HotelAgent(llm),
        activity_agent=ActivityAgent(llm, retriever=RetrieverService(SentenceTransformerProvider())),
        weather_agent=WeatherAgent(llm),
        budget_agent=BudgetAgent(llm),
        constraint_agent=ConstraintAgent(llm),
    )

async def run_workflow(
    graph, request: TravelRequest, user_id: int | None = None, memory_service: MemoryService | None = None,
) -> TravelState:
    preferences_text = None
    if memory_service and user_id:
        prefs = await memory_service.get_preferences(user_id)
        if prefs:
            preferences_text = "; ".join(f"{p.key}: {p.value}" for p in prefs)

    initial = GraphState(request=request, preferences=preferences_text)
    result = await graph.ainvoke(initial)
    state = TravelState.model_validate(dict(result))

    if state.status == "completed" and memory_service and user_id:
        await memory_service.save_trip(user_id, state)

    return state