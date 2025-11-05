Here’s the complete README.md file content (you can copy-paste it directly):

⸻


# 🧭 Travel Planner Agent (LangGraph + FastAPI)

This project implements a **multi-agent travel itinerary planner** using **LangGraph** for agent orchestration and **FastAPI** for API serving.

It autonomously generates optimized travel itineraries based on:
- **Weather predictions** (simulated)
- **Budget tiers** (Low / Mid / High)
- A **Supervisor agent** that merges all results
- A **Replanning agent** that regenerates plans if flights are delayed >6 hours
- **Itinerary history tracking** to show previous versions after replanning

---

## 🚀 Features

- **Supervisor agent**: Orchestrates sub-agents (weather + budget).
- **Weather agent**: Predicts random weather and selects suitable indoor/outdoor activities.
- **Budget agent**: Chooses trip plans based on price tiers (<25K, 25–75K, >75K).
- **Merge supervisor**: Combines both branches to build a full itinerary.
- **Replanning agent**: Automatically re-triggers the flow once if flight delay >6 hours.
- **History tracking**: Preserves previous itineraries before replan.

---

## ⚙️ Installation

```bash
python -m venv .venv
source .venv/bin/activate   # (Windows) .venv\Scripts\activate
pip install -r requirements.txt


⸻

▶️ Running the API

Start the FastAPI server:

uvicorn travel_api:app --reload

Then visit:
	•	Swagger UI: http://127.0.0.1:8000/docs
	•	Redoc: http://127.0.0.1:8000/redoc

⸻

🌐 Endpoint

POST /plan

Request Body

{
  "destination": "Goa",
  "travel_date": "2025-12-20",
  "budget": 85000,
  "flight_delay_hours": 7
}

Example curl

curl -X POST http://127.0.0.1:8000/plan \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "travel_date": "2025-12-20",
    "budget": 90000,
    "flight_delay_hours": 7
  }'


⸻

📦 Sample Response

{
  "destination": "Goa",
  "travel_date": "2025-12-20",
  "budget": 90000,
  "weather_summary": "sunny",
  "budget_tier": "high",
  "final_itinerary": [
    "Destination: Goa",
    "Predicted weather: sunny",
    "Budget tier: high",
    "=== Core (budget-based) plan ===",
    "5-star / luxury resort in Goa",
    "Private cab for whole day",
    "Premium beach club entry",
    "Fine dining dinner",
    "=== Weather-aware suggestions ===",
    "Morning beach time at Goa",
    "Water sports (parasailing / jet ski)",
    "Evening cruise / sunset point",
    "Extra: Book a private sunset cruise."
  ],
  "itinerary_history": [],
  "replan_count": 1
}


⸻

🧠 Graph Workflow

Topology

START
  ↓
Supervisor Orchestrator
  ├──▶ Weather Agent
  └──▶ Budget Agent
         ↓        ↓
           └──▶ Supervisor Merge
                   ↓
             Replanning Agent
                 ├── replan=True  → Supervisor Orchestrator
                 └── replan=False → END

Each node updates only its part of the state (avoids concurrent write conflicts).
The merge node builds a final itinerary when both branches complete.

⸻

🧩 Components

Agent	Role	Input	Output
Supervisor Orchestrator	Initializes base state, routes graph	destination, date, budget	normalized state
Weather Agent	Predicts weather + suggests activities	destination, date	weather_summary, weather_activities
Budget Agent	Suggests stay & plan based on budget	destination, budget	budget_tier, budget_plan
Merge Supervisor	Combines results, adds cross-logic	all above	final_itinerary, itinerary_history
Replanning Agent	Checks delay >6h and triggers replan	flight_delay_hours	replan_required


⸻

🛠️ Customization
	•	🔗 Integrate real APIs
	•	Replace the dummy weather_tool() with OpenWeather or Tomorrow.io.
	•	Load budget itineraries dynamically from a database.
	•	🤖 Add LLM reasoning
	•	Bind LangChain tools to Bedrock or OpenAI:

from langchain_aws import ChatBedrock
llm = ChatBedrock(model_id="anthropic.claude-3-sonnet")
llm = llm.bind_tools([get_weather, get_budget_plan])


	•	Replace deterministic nodes with LLM-powered ones.

	•	🔁 Multi-replan logic
	•	Change the condition in replanning_agent to replan_count < N.
	•	🔐 Secure the API
	•	Add JWT-based authentication (FastAPI dependency injection).
	•	Log each request for auditing or analytics.

⸻

📜 Requirements

See requirements.txt:

fastapi==0.115.5
uvicorn[standard]==0.32.1
langgraph==0.2.53
langchain-core==0.3.26
typing-extensions>=4.12.2
pydantic==2.9.2


⸻

🧾 License

MIT License — free to modify and use.

⸻

Author

Swapnanil Sharmah
