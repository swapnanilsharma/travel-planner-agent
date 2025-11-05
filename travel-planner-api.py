from __future__ import annotations
from typing import TypedDict, List, Literal, Dict, Any, Optional
import random

from fastapi import FastAPI
from pydantic import BaseModel

from langgraph.graph import StateGraph, START, END


# ======================================================
# 1) LangGraph state
# ======================================================

class TravelState(TypedDict, total=False):
    destination: str
    travel_date: str
    budget: int
    flight_delay_hours: int

    # weather branch
    weather_summary: str
    weather_activities: List[str]

    # budget branch
    budget_tier: str
    budget_plan: List[str]

    # final / versions
    final_itinerary: List[str]
    itinerary_history: List[List[str]]

    # replanning
    replan_required: bool
    replan_count: int


# ======================================================
# 2) Dummy/random tools
# ======================================================

def weather_tool(travel_date: str, destination: str) -> Dict[str, Any]:
    possible = ["sunny", "clear", "overcast", "rainy", "stormy", "humid"]
    summary = random.choice(possible)
    temp = random.choice(["27C", "29C", "30C", "32C"])
    return {"summary": summary, "temperature": temp}


def budget_tool_low(destination: str) -> List[str]:
    options = [
        [
            f"Check-in to budget homestay near {destination} beach",
            "Visit public beach",
            "Street food",
            "Evening walk",
        ],
        [
            f"Backpacker hostel in {destination}",
            "Scooter rental (shared)",
            "Free fort / viewpoint",
            "Budget café",
        ],
    ]
    return random.choice(options)


def budget_tool_mid(destination: str) -> List[str]:
    options = [
        [
            f"3-star resort in {destination}",
            "Water sports (shared)",
            "Sunset cruise",
            "Mid-range restaurant",
        ],
        [
            f"Boutique hotel in {destination}",
            "Daytime sightseeing",
            "Evening beach shacks",
            "Taxi for local commute",
        ],
    ]
    return random.choice(options)


def budget_tool_high(destination: str) -> List[str]:
    options = [
        [
            f"5-star / luxury resort in {destination}",
            "Private cab for whole day",
            "Premium beach club entry",
            "Fine dining dinner",
        ],
        [
            f"Luxury villa stay in {destination}",
            "Private boat / cruise",
            "Spa session",
            "High-end nightlife",
        ],
    ]
    return random.choice(options)


# ======================================================
# 3) LangGraph nodes (same as before, API-safe)
# ======================================================

def supervisor_orchestrator(state: TravelState) -> TravelState:
    out: TravelState = {}
    if "destination" not in state:
        out["destination"] = "Goa"
    if "travel_date" not in state:
        out["travel_date"] = "2025-12-20"
    if "budget" not in state:
        out["budget"] = 20000
    if "flight_delay_hours" not in state:
        out["flight_delay_hours"] = 0
    if "replan_count" not in state:
        out["replan_count"] = 0
    if "itinerary_history" not in state:
        out["itinerary_history"] = []
    return out


def weather_agent(state: TravelState) -> TravelState:
    destination = state["destination"]
    travel_date = state["travel_date"]
    w = weather_tool(travel_date, destination)
    summary = w["summary"]

    if summary in ("sunny", "clear"):
        pool = [
            f"Morning beach time at {destination}",
            "Water sports (parasailing / jet ski)",
            "Island / boat trip",
            "Evening cruise / sunset point",
        ]
    elif summary in ("overcast", "humid"):
        pool = [
            "Late-morning sightseeing (fort / churches)",
            "Café hopping",
            "Local market visit",
            "Evening at beach shacks",
        ]
    else:
        pool = [
            "Indoor spa / wellness session",
            "Museum / cultural center",
            "Cooking class / local tasting",
            "Indoor games at stay",
        ]

    k = 3 if len(pool) >= 3 else len(pool)
    activities = random.sample(pool, k=k)

    return {
        "weather_summary": summary,
        "weather_activities": activities,
    }


def budget_agent(state: TravelState) -> TravelState:
    destination = state["destination"]
    budget = state["budget"]

    if budget < 25000:
        tier = "low"
        plan = budget_tool_low(destination)
    elif 25000 <= budget <= 75000:
        tier = "mid"
        plan = budget_tool_mid(destination)
    else:
        tier = "high"
        plan = budget_tool_high(destination)

    return {
        "budget_tier": tier,
        "budget_plan": plan,
    }


def supervisor_merge(state: TravelState) -> TravelState:
    has_weather = "weather_activities" in state
    has_budget = "budget_plan" in state
    if not (has_weather and has_budget):
        return {}

    destination = state["destination"]
    weather_summary = state["weather_summary"]
    budget_tier = state["budget_tier"]
    budget_plan = state["budget_plan"]
    weather_acts = state["weather_activities"]

    new_plan: List[str] = []
    new_plan.append(f"Destination: {destination}")
    new_plan.append(f"Predicted weather: {weather_summary}")
    new_plan.append(f"Budget tier: {budget_tier}")

    new_plan.append("=== Core (budget-based) plan ===")
    new_plan.extend(budget_plan)

    new_plan.append("=== Weather-aware suggestions ===")
    new_plan.extend(weather_acts)

    # cross logic
    if weather_summary in ("sunny", "clear") and budget_tier == "high":
        new_plan.append("Extra: Book a private sunset cruise.")
    elif weather_summary in ("rainy", "stormy") and budget_tier == "low":
        new_plan.append("Extra: Pick indoor-friendly, low-cost activities.")
    elif weather_summary in ("overcast", "humid") and budget_tier == "mid":
        new_plan.append("Extra: Do sightseeing in morning, café later.")

    history = list(state.get("itinerary_history", []))
    if "final_itinerary" in state:
        history.append(state["final_itinerary"])

    return {
        "final_itinerary": new_plan,
        "itinerary_history": history,
    }


def replanning_agent(state: TravelState) -> TravelState:
    delay = state.get("flight_delay_hours", 0)
    replan_count = state.get("replan_count", 0)
    if delay > 6 and replan_count == 0:
        return {
            "replan_required": True,
            "replan_count": replan_count + 1,
        }
    else:
        return {
            "replan_required": False,
            "replan_count": replan_count,
        }


def needs_replan(state: TravelState) -> Literal["REPLAN", "DONE"]:
    if state.get("replan_required"):
        return "REPLAN"
    return "DONE"


def build_travel_graph():
    graph = StateGraph(TravelState)

    graph.add_node("supervisor_orchestrator", supervisor_orchestrator)
    graph.add_node("weather_agent", weather_agent)
    graph.add_node("budget_agent", budget_agent)
    graph.add_node("supervisor_merge", supervisor_merge)
    graph.add_node("replanning_agent", replanning_agent)

    graph.add_edge(START, "supervisor_orchestrator")
    graph.add_edge("supervisor_orchestrator", "weather_agent")
    graph.add_edge("supervisor_orchestrator", "budget_agent")
    graph.add_edge("weather_agent", "supervisor_merge")
    graph.add_edge("budget_agent", "supervisor_merge")
    graph.add_edge("supervisor_merge", "replanning_agent")

    graph.add_conditional_edges(
        "replanning_agent",
        needs_replan,
        {
            "REPLAN": "supervisor_orchestrator",
            "DONE": END,
        },
    )

    return graph.compile()


# ======================================================
# 4) FastAPI layer
# ======================================================

app = FastAPI(title="Travel Itinerary Agent API")

# build and keep the graph in memory
travel_graph = build_travel_graph()


class PlanRequest(BaseModel):
    destination: Optional[str] = "Goa"
    travel_date: Optional[str] = "2025-12-20"
    budget: Optional[int] = 45000
    flight_delay_hours: Optional[int] = 0


class PlanResponse(BaseModel):
    destination: str
    travel_date: str
    budget: int
    weather_summary: str | None = None
    budget_tier: str | None = None
    final_itinerary: List[str]
    itinerary_history: List[List[str]]
    replan_count: int


@app.post("/plan", response_model=PlanResponse)
def plan_trip(req: PlanRequest):
    # feed request into graph
    state_in: TravelState = {
        "destination": req.destination,
        "travel_date": req.travel_date,
        "budget": req.budget,
        "flight_delay_hours": req.flight_delay_hours,
    }

    # you can tune recursion_limit if you want
    state_out = travel_graph.invoke(state_in, config={"recursion_limit": 50})

    return PlanResponse(
        destination=state_out["destination"],
        travel_date=state_out["travel_date"],
        budget=state_out["budget"],
        weather_summary=state_out.get("weather_summary"),
        budget_tier=state_out.get("budget_tier"),
        final_itinerary=state_out.get("final_itinerary", []),
        itinerary_history=state_out.get("itinerary_history", []),
        replan_count=state_out.get("replan_count", 0),
    )
