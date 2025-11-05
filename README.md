# 🧭 Travel Planner Agent (LangGraph + FastAPI)

A multi-agent travel itinerary planner built with **LangGraph** for agent orchestration and **FastAPI** for API serving. It generates optimized travel plans based on:

- 🌤️ Simulated weather predictions
- 💰 Budget tiers (Low / Mid / High)
- 🧠 Supervisor agent to merge results
- 🔁 Replanning agent for flight delays >6 hours
- 🕓 Itinerary history tracking

---

## 🚀 Features

- **Supervisor Agent**: Coordinates the planning workflow.
- **Weather Agent**: Simulates weather and suggests indoor/outdoor activities.
- **Budget Agent**: Recommends plans based on budget tiers:
  - Low: < ₹25,000
  - Mid: ₹25,000–₹75,000
  - High: > ₹75,000
- **Merge Supervisor**: Combines weather and budget plans into a final itinerary.
- **Replanning Agent**: Triggers replanning if flight delay exceeds 6 hours.
- **History Tracking**: Stores previous itineraries before replanning.

---

## ⚙️ Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ▶️ Running the API

Start the FastAPI server:

```bash
uvicorn travel_api:app --reload
```

Access the documentation:

- 🔍 Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📘 Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🌐 API Endpoint

### POST /plan

Request Body:

```json
{
  "destination": "Goa",
  "travel_date": "2025-12-20",
  "budget": 85000,
  "flight_delay_hours": 7
}
```

Example cURL:

```bash
curl -X POST http://127.0.0.1:8000/plan \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "travel_date": "2025-12-20",
    "budget": 90000,
    "flight_delay_hours": 7
  }'
```

---

## 📦 Sample Response

```json
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
```

---

## 🧠 Graph Workflow

```text
START
  ↓
Supervisor Orchestrator
  ├──▶ Weather Agent
  └──▶ Budget Agent
         ↓        ↓
           └──▶ Merge Supervisor
                   ↓
             Replanning Agent
                 ├── replan = True  → Supervisor Orchestrator
                 └── replan = False → END
```

- Each node updates only its part of the state to avoid conflicts.
- The merge node finalizes the itinerary once both branches complete.

---

## 🧩 Agent Components

| Agent                | Role                                      | Input                        | Output                             |
|---------------------|-------------------------------------------|------------------------------|------------------------------------|
| Supervisor Orchestrator | Initializes state, routes graph         | destination, date, budget    | normalized state                   |
| Weather Agent        | Predicts weather, suggests activities     | destination, date            | weather_summary, weather_activities |
| Budget Agent         | Suggests plan based on budget             | destination, budget          | budget_tier, budget_plan           |
| Merge Supervisor     | Combines results, adds logic              | all above                    | final_itinerary, itinerary_history |
| Replanning Agent     | Checks delay, triggers replan if needed   | flight_delay_hours           | replan_required                    |

---

## 🛠️ Customization Ideas

- 🔗 **Integrate Real APIs**:
  - Replace `weather_tool()` with OpenWeather or Tomorrow.io.
  - Load budget plans from a database.

- 🤖 **Add LLM Reasoning**:
  ```python
  from langchain_aws import ChatBedrock
  llm = ChatBedrock(model_id="anthropic.claude-3-sonnet")
  llm = llm.bind_tools([get_weather, get_budget_plan])
  ```

- 🔁 **Multi-Replan Logic**:
  - Modify `replanning_agent` to allow multiple replans (e.g., `replan_count < N`).

- 🔐 **Secure the API**:
  - Add JWT-based authentication via FastAPI dependencies.
  - Log requests for auditing and analytics.

---

## 📜 Requirements

From `requirements.txt`:

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
langgraph==0.2.53
langchain-core==0.3.26
typing-extensions>=4.12.2
pydantic==2.9.2
```

---

## 🧾 License

MIT License — free to use and modify.

---

## 👤 Author

**Swapnanil Sharmah**

---
