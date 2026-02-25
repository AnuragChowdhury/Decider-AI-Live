# 📘 Decidra — Developer README

## 1. What is this project?

Decidra is an **AI-powered decision intelligence system**.

It is **not**:
- a traditional BI tool
- a simple chatbot
- a static dashboard application

It **is**:
- an agent-driven backend system
- that understands **any kind of dataset**
- dynamically mutates dashboards
- and **recommends decisions**, not just charts

The frontend is intentionally kept dumb.  
All intelligence lives in the backend.

---

## 2. Core Philosophy (READ THIS FIRST)

> **Agents THINK, Tools DO, Schemas DEFINE, APIs ROUTE, Frontend RENDERS**

If you follow this rule, the system stays clean and scalable.

---

## 3. High-Level Architecture

Frontend (React – AI Generated)
↕
Backend (FastAPI)
↕
Agent Runtime (Orchestrator + Agents)
↕
Tool Layer (Deterministic Execution)
↕
Data (CSV / Excel / DB / Models)

⚠️ This is **NOT** a classic frontend-backend-database app.  
The database is a **resource**, not the brain.

---

## 4. Repository Structure



```text
backend/
├── main.py
│   # FastAPI entry point
│   # - Initializes the FastAPI app
│   # - Registers API routers
│   # - Sets up global configuration
│   # - NO business logic or intelligence here
│
├── api/
│   # Thin HTTP layer (NO intelligence)
│   # Responsible only for request routing and response formatting
│
│   ├── chat.py
│   │   # Chat endpoint
│   │   # - Accepts user chat messages
│   │   # - Forwards input to Agent Orchestrator
│   │   # - Returns orchestrator response to frontend
│   │
│   ├── upload.py
│   │   # Data upload endpoint
│   │   # - Accepts CSV / Excel files
│   │   # - Stores raw data in system state
│   │   # - Triggers initial orchestration flow
│   │
│   └── dashboard.py
│       # Dashboard state API
│       # - Stores and serves dashboard JSON
│       # - Acts as single source of truth for dashboard state
│       # - Does NOT compute analytics or decide charts
│
├── agents/
│   # Intelligence layer (ALL reasoning lives here)
│
│   ├── orchestrator.py
│   │   # Central decision-maker
│   │   # - Detects user intent
│   │   # - Decides which agents to run
│   │   # - Controls execution order
│   │   # - Merges agent outputs into final response
│
│   ├── data_agent.py
│   │   # Data validation & profiling agent
│   │   # - Detects data structure and quality
│   │   # - Identifies time dimension (if any)
│   │   # - Determines allowed / blocked capabilities
│
│   ├── analytics_agent.py
│   │   # Descriptive analytics agent
│   │   # - KPIs, aggregations, comparisons
│   │   # - Facts only (NO prediction or decisions)
│
│   ├── prediction_agent.py
│   │   # Forecasting agent
│   │   # - Runs predictions when data supports it
│   │   # - Computes confidence & uncertainty
│   │   # - Can refuse to predict if data is invalid
│
│   ├── decision_agent.py
│   │   # Decision recommendation agent
│   │   # - Root cause reasoning
│   │   # - What-if simulations
│   │   # - Generates actionable recommendations
│
│   ├── ui_agent.py
│   │   # UI Controller Agent
│   │   # - Mutates dashboard JSON
│   │   # - Adds/removes charts
│   │   # - Highlights anomalies and insights
│
│   └── explanation_agent.py
│       # Explainability & trust agent
│       # - Converts outputs into business-friendly explanations
│       # - Lists assumptions, risks, and reasoning
│
├── tools/
│   # Safe execution layer (NO reasoning, NO LLMs)
│
│   ├── data_tools.py
│   │   # Data loading, profiling, cleaning utilities
│
│   ├── analytics_tools.py
│   │   # KPI computation, aggregations, filters
│
│   ├── prediction_tools.py
│   │   # Forecasting models and confidence intervals
│
│   ├── simulation_tools.py
│   │   # What-if analysis and scenario simulations
│
│   └── dashboard_tools.py
│       # Safe dashboard JSON mutation utilities
│
├── core/
│   # Shared infrastructure and contracts
│
│   ├── schemas.py
│   │   # Shared data contracts
│   │   # - Request/response models
│   │   # - AgentResult, OrchestratorResponse
│   │   # - Dashboard JSON schema
│
│   └── state.py
│       # In-memory system state
│       # - Dataset
│       # - Data profile metadata
│       # - Dashboard state
│       # - Chat memory
│
└── README.md
    # Developer documentation
    # Architecture, rules, and contribution guidelines


---
```

## 5. File Responsibilities (IMPORTANT)

### `main.py`
- FastAPI app initialization
- Router registration
- App-level configuration  
❌ No business logic

---

### `api/*`
**Purpose:** Request routing only

- Accept HTTP requests
- Forward data to orchestrator
- Return orchestrator response

❌ No analytics  
❌ No agent logic  
❌ No data processing  

---

### `agents/orchestrator.py`
**THE BRAIN**

Responsibilities:
- Detect user intent
- Decide which agents should run
- Control execution order
- Merge agent outputs into one response

Important rules:
- Orchestrator decides, agents execute
- Uses rules first, LLM later
- Never accesses data directly

---

### `agents/data_agent.py`
- Profiles uploaded dataset
- Detects structure (time-series, snapshot, etc.)
- Determines allowed / blocked capabilities

This agent **protects system correctness**.

---

### `agents/analytics_agent.py`
- Performs descriptive analytics only
- KPIs, aggregations, comparisons

❌ No forecasting  
❌ No decisions  

---

### `agents/prediction_agent.py`
- Performs forecasting when valid
- Computes confidence intervals
- Can refuse to predict

Runs **only if time dimension exists**.

---

### `agents/decision_agent.py`
- Converts analytics into actions
- Root-cause reasoning
- What-if simulations
- Risk & confidence assessment

❌ Does NOT modify dashboard

---

### `agents/ui_agent.py`
- Modifies dashboard JSON
- Adds/removes charts
- Highlights anomalies
- Annotates insights

⚠️ Only agent allowed to mutate dashboard state.

---

### `agents/explanation_agent.py`
- Explains insights in business language
- Lists assumptions & risks
- Builds trust

❌ No analytics  
❌ No decisions  

---

### `tools/*`
**Deterministic execution layer**

- Tools perform actual computation
- No reasoning
- No LLM usage

Agents NEVER write raw pandas / SQL — they call tools.

Tool split:
- `data_tools.py` → loading, profiling, cleaning
- `analytics_tools.py` → KPIs, aggregations
- `prediction_tools.py` → forecasting
- `simulation_tools.py` → what-if analysis
- `dashboard_tools.py` → dashboard JSON mutation

---

### `core/schemas.py`
**System contracts**

- Defines request/response formats
- Defines AgentResult, OrchestratorResponse
- Defines dashboard JSON shape

⚠️ Changing schemas affects entire system.

---

### `core/state.py`
**System memory**

Stores:
- Dataset
- Data profile
- Dashboard state
- Chat memory

⚠️ Not a database. Simple and replaceable.

---

## 6. Dashboard Philosophy

- Dashboard is **JSON**, not UI logic
- Backend owns dashboard state
- UI Agent mutates dashboard JSON
- Frontend renders exactly what it receives

This enables **self-mutating dashboards**.

---

## 7. Data Flexibility (VERY IMPORTANT)

- Users can upload **any dataset**
- No fixed schema required
- System adapts capabilities based on data shape

Examples:
- No date column → no forecasting
- Snapshot data → comparisons & segmentation
- Time-series → trends & predictions

The system **never hallucinates structure**.

---

## 8. Development Rules (NON-NEGOTIABLE)

1. Agents never call other agents
2. Agents never access data directly
3. Tools never contain reasoning
4. Frontend never computes analytics
5. Orchestrator is the only decision-maker

If confused, follow:
> Intelligence → Agents  
> Execution → Tools  
> State → dashboard.py  

---

## 9. MVP Focus (DO NOT OVERBUILD)

For initial version:
- Upload CSV
- Basic dashboard JSON
- Chat endpoint
- Dummy agents
- Dummy orchestrator

Intelligence comes later.  
Infrastructure comes first.

---

## 10. Final Note

This project is designed as a **learning-grade but production-shaped system**.

If something feels complex:
- simplify
- do not break contracts
- do not move intelligence into the frontend

---

**Welcome to Decidra. Build slow. Build right.**
