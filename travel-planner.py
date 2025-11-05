from typing import TypedDict, List, Literal, Dict, Any
from langgraph.graph import StateGraph, START, END
import random


# =========================
# 1. State
# =========================

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
    final_itinerary: List[str]              # latest
    itinerary_history: List[List[str]]      # previous versions

    # replanning
    replan_required: bool
    replan_count: int


# =========================
# 2. Tools
# =========================

def weather_tool(travel_date: str, destination: str) -> Dict[str, Any]:
    """
    Dummy weather tool with some variety.
    """
    possible = ["sunny", "clear", "overcast", "rainy", "stormy", "humid"]
    summary = random.choice(possible)
    temp = random.choice(["27C", "29C", "30C", "32C"])
    return {"summary": summary, "temperature": temp}


def budget_tool_low(destination: str) -> List[str]:
    # give some variety for low budget
    options = [
        [
            f"Check-in to budget homestay near {destination} beach",
            "Visit public beach (Calangute / Miramar equivalent)",
            "Local street food / fish thali",
            "Evening walk at beach",
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
            "Water sports pack (shared)",
            "Sunset cruise",
            "Popular mid-range restaurant",
        ],
        [
            f"Business/boutique hotel in {destination}",
            "Daytime sightseeing (church/fort)",
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
            "Fine dining seafood dinner",
        ],
        [
            f"Luxury villa stay in {destination}",
            "Private boat / cruise booking",
            "Spa session",
            "High-end nightlife / lounge",
        ],
    ]
    return random.choice(options)


# =========================
# 3. Agents
# =========================

def supervisor_orchestrator(state: TravelState) -> TravelState:
    """
    Top node: normalize inputs.
    IMPORTANT: only fill missing keys, don't overwrite on replan.
    """
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
    """
    Pick random weather and then map to activities.
    """
    destination = state["destination"]
    travel_date = state["travel_date"]

    w = weather_tool(travel_date, destination)
    summary = w["summary"]

    # weather → activity pool
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
            "Café hopping (air-conditioned)",
            "Local market visit",
            "Evening at beach shacks",
        ]
    else:  # rainy, stormy
        pool = [
            "Indoor spa / wellness session",
            "Museum / cultural center",
            "Cooking class / local cuisine tasting",
            "Indoor board games at stay",
        ]

    # pick 2-3 out of pool for variety
    k = 3 if len(pool) >= 3 else len(pool)
    activities = random.sample(pool, k=k)

    return {
        "weather_summary": summary,
        "weather_activities": activities,
    }


def budget_agent(state: TravelState) -> TravelState:
    """
    Pick plan list based on budget.
    """
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
    """
    Build final itinerary ONLY when both weather and budget are available.
    Also preserve old plan in itinerary_history.
    Add small cross-logic: sunny + high budget → premium outdoor;
                          rainy + low budget → indoor + cheap.
    """
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

    # cross-suggestions
    if weather_summary in ("sunny", "clear") and budget_tier == "high":
        new_plan.append("Extra (sunny+high): Book a private sunset cruise.")
        new_plan.append("Extra (sunny+high): Reserve a table at a beach club.")
    elif weather_summary in ("rainy", "stormy") and budget_tier == "low":
        new_plan.append("Extra (rainy+low): Pick a hostel/café with indoor games.")
        new_plan.append("Extra (rainy+low): Do short local food trail under shade.")
    elif weather_summary in ("overcast", "humid") and budget_tier == "mid":
        new_plan.append("Extra (overcast+mid): Do forts/churches in the morning and café later.")
        new_plan.append("Extra (overcast+mid): Keep a taxi/scooter flexible.")

    # handle history
    history = list(state.get("itinerary_history", []))
    if "final_itinerary" in state:
        history.append(state["final_itinerary"])

    return {
        "final_itinerary": new_plan,
        "itinerary_history": history,
    }


def replanning_agent(state: TravelState) -> TravelState:
    """
    Replan once if delay>6h.
    """
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


# =========================
# 4. Routing
# =========================

def needs_replan(state: TravelState) -> Literal["REPLAN", "DONE"]:
    if state.get("replan_required"):
        return "REPLAN"
    return "DONE"


# =========================
# 5. Build graph
# =========================

def build_travel_graph():
    graph = StateGraph(TravelState)

    graph.add_node("supervisor_orchestrator", supervisor_orchestrator)
    graph.add_node("weather_agent", weather_agent)
    graph.add_node("budget_agent", budget_agent)
    graph.add_node("supervisor_merge", supervisor_merge)
    graph.add_node("replanning_agent", replanning_agent)

    # root
    graph.add_edge(START, "supervisor_orchestrator")

    # fan-out
    graph.add_edge("supervisor_orchestrator", "weather_agent")
    graph.add_edge("supervisor_orchestrator", "budget_agent")

    # both to merge
    graph.add_edge("weather_agent", "supervisor_merge")
    graph.add_edge("budget_agent", "supervisor_merge")

    # merge -> replanning
    graph.add_edge("supervisor_merge", "replanning_agent")

    # conditional
    graph.add_conditional_edges(
        "replanning_agent",
        needs_replan,
        {
            "REPLAN": "supervisor_orchestrator",
            "DONE": END,
        },
    )

    return graph.compile()


# =========================
# 6. Run
# =========================

if __name__ == "__main__":

    app = build_travel_graph()

    initial_state: TravelState = {
        "destination": "Goa",
        "travel_date": "2025-12-20",
        "budget": 85000,
        "flight_delay_hours": 7,
    }

    final_state = app.invoke(initial_state)

    print("=== LATEST PLAN ===")
    for line in final_state.get("final_itinerary", []):
        print("  -", line)

    print("\n=== PREVIOUS PLANS ===")
    for idx, old in enumerate(final_state.get("itinerary_history", []), start=1):
        print(f"\n  Plan #{idx}:")
        for line in old:
            print("    -", line)

    print("\nreplan_count:", final_state.get("replan_count"))
    print("weather:", final_state.get("weather_summary"))
    print("budget_tier:", final_state.get("budget_tier"))
