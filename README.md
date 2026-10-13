# Ryde Dispute Resolver

Multi-agent autonomous dispute resolution system for the **Ryde** ride-hailing platform, built for the **Tencent Cloud AI Singapore Hackathon 2026**.

Three LLM-powered agents — a **Rider Advocate**, a **Driver Advocate**, and a **Judge** — resolve rider-driver disputes by independently gathering evidence, arguing their case against company policy, and issuing a binding ruling with dual explanations.

---

## Architecture

```
                         ┌─────────────────┐
                         │  START          │
                         └────┬──────┬─────┘
                              │      │
                    ┌─────────┘      └─────────┐
                    ▼                            ▼
          ┌──────────────────┐        ┌──────────────────┐
          │  Rider Advocate  │        │ Driver Advocate  │   Phase 1: Parallel
          │  (gathers        │        │  (gathers        │   evidence gathering
          │   evidence)      │        │   evidence)      │
          └────────┬─────────┘        └────────┬─────────┘
                   │                           │
                   ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │  Rider Rebuttal  │        │ Driver Rebuttal  │   Phase 2: Rebuttal
          │  (counters       │        │  (counters       │   (see opponent's arg)
          │   driver's case) │        │   rider's case)  │
          └────────┬─────────┘        └────────┬─────────┘
                   │                           │
                   └──────────┬──────────────-┘
                              ▼
                    ┌──────────────────┐
                    │     Judge        │               Phase 3: Ruling
                    │  (verifies,      │               (weighs arguments +
                    │   applies policy)│                rebuttals)
                    └────────┬─────────┘
                             │
                             ▼
                       ┌──────────┐
                       │   END    │
                       └──────────┘
```

The pipeline uses a **LangGraph diamond-shaped state machine**:
- **Phase 1**: Both advocates run **in parallel**, each independently calling evidence tools and building a structured argument.
- **Phase 2**: Each advocate sees the other's argument and produces a **rebuttal** with specific counterpoints.
- **Phase 3**: The **Judge** reviews both arguments and rebuttals, independently verifies key claims via tools, applies company policy, and issues a ruling.

---

## Features

- **2-step LLM pipeline per agent**: (1) LLM decides which tools to call, (2) LLM analyzes tool results and produces structured JSON output
- **5 evidence tools**: GPS route analysis, chat log sentiment, fare validation, user history, company policy
- **4 sample disputes** covering 2 dispute types (route deviation + no-show charge)
- **Company policy document** with citeable sub-clauses (Sections 1.1–3.5)
- **Interactive route map** showing actual vs optimal GPS routes
- **Demo mode** (rule-based, no API key needed) + **Live mode** (real LLM calls)
- **Color-coded conversation log** with per-agent colors and message-type icons
- **Final ruling card** with decision badge, confidence gauge, and dual explanations

---

## Quick Start

```bash
# Clone
git clone https://github.com/ngkokchen/tencent-cloud-ai-hackathon.git
cd tencent-cloud-ai-hackathon

# Install dependencies
pip install -r requirements.txt

# Run the app (demo mode works without any API key)
streamlit run app/ui.py
```

Open http://localhost:8501, pick a sample case from the sidebar, and click **Resolve Dispute**.

### Docker

```bash
docker compose up --build
```

The app will be available at http://localhost:8501. To use live mode, mount your `.env` file (already handled by docker-compose.yml).

### Running Tests

```bash
pip install pytest
pytest tests/ -v
```

All 18 tests run in demo mode (no API key needed).

### Live Mode (with real LLM)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set your LLM credentials:
   ```env
   LLM_API_BASE=https://api.hunyuan.cloud.tencent.com/v1   # Tencent Hunyuan
   LLM_API_KEY=your-api-key
   LLM_MODEL=hunyuan-pro
   ```
3. Uncheck "Demo mode" in the sidebar UI.

Works with any OpenAI-compatible endpoint (Tencent Hunyuan, OpenAI, DeepSeek, etc.).

---

## Sample Cases

| Case ID | Type | Description | Expected Ruling |
|---------|------|-------------|-----------------|
| RD-2026-001 | Route deviation | 57% deviation, no traffic justification, no communication | Refund $6.38 |
| RD-2026-002 | Route deviation | 11% deviation, traffic exception applies, driver communicated | No action |
| NS-2026-001 | No-show | Rider 120m away, driver waited 6 min, contacted 3x | No action |
| NS-2026-002 | No-show | Rider at pickup, driver left after 2 min | Refund $5.00 |

---

## Project Structure

```
.
├── agents/
│   ├── base.py                  # BaseAgent: tool calling, LLM interaction, logging
│   ├── rider_advocate.py        # Rider Advocate: run() + rebut()
│   ├── driver_advocate.py       # Driver Advocate: run() + rebut()
│   ├── judge.py                 # Judge: run() with argument + rebuttal inputs
│   └── prompts/
│       ├── rider_advocate.md    # Pro-rider system prompt
│       ├── driver_advocate.md   # Pro-driver system prompt
│       ├── rider_rebuttal.md    # Rider rebuttal instructions
│       ├── driver_rebuttal.md   # Driver rebuttal instructions
│       └── judge.md             # Neutral judge system prompt
├── app/
│   ├── ui.py                    # Main Streamlit page
│   └── components/
│       ├── dispute_form.py      # Sidebar: sample picker + custom filing
│       ├── message_log.py       # Color-coded conversation timeline
│       ├── ruling_panel.py      # Ruling card with confidence gauge
│       ├── evidence_panel.py    # Evidence summary + route map
│       └── route_map.py         # Folium map: actual vs optimal route
├── config/
│   └── settings.py              # Fare rates, thresholds, paths
├── data/
│   ├── policies/
│   │   └── ryde_policy.md       # Company policy (citeable sections)
│   └── samples/
│       ├── index.json           # Case index for UI
│       ├── route_deviation_clear.json
│       ├── route_deviation_borderline.json
│       ├── no_show_genuine.json
│       └── no_show_disputed.json
├── evidence/
│   ├── loaders.py               # CaseData dataclass + case index
│   ├── gps.py                   # Haversine, route analysis, traffic exception
│   ├── chat.py                  # Sentiment, threat detection, contact dynamics
│   ├── fare.py                  # Fare validation, anomaly detection, overcharge
│   └── history.py               # Risk indicators, recurring patterns
├── graph/
│   ├── state.py                 # LangGraph DisputeState schema
│   ├── langgraph_orchestrator.py # Diamond-shaped graph (live mode)
│   ├── orchestrator.py          # Demo mode + live mode entry point
│   └── tools.py                 # 5 tool functions + TOOL_REGISTRY
├── llm/
│   └── client.py                # OpenAI-compatible LLM wrapper
├── models/
│   ├── message.py               # AgentMessage + ConversationLog
│   ├── argument.py              # Argument, EvidenceItem, PolicyCitation, Rebuttal
│   └── ruling.py                # Ruling (decision, amount, confidence, dual explanations)
├── tests/
│   ├── test_route_deviation.py  # Route deviation end-to-end tests
│   ├── test_no_show.py          # No-show end-to-end tests
│   └── test_message_log.py      # Message logging verification
├── .env.example
├── .gitignore
├── .dockerignore
├── ARCHITECTURE.md
├── Dockerfile                   # Container deployment
├── docker-compose.yml           # One-command deploy
├── requirements.txt
└── run.py
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Agent Framework | LangGraph (diamond state machine) |
| LLM Provider | Tencent Cloud Hunyuan (OpenAI-compatible) |
| Data Models | Pydantic v2 |
| UI | Streamlit + Folium (interactive maps) |
| State Management | LangGraph TypedDict state |

---

## How It Works

### Agent Pipeline

Each advocate follows a **2-step LLM pipeline**:
1. **Tool selection**: The LLM receives the dispute summary and available tool descriptions, then decides which tools to call and why.
2. **Analysis**: The LLM receives the tool results and produces a structured JSON argument with: claim, evidence list, policy citations, requested remedy, and reasoning.

The Judge follows the same pattern but selects **verification tools** to independently check the advocates' claims before ruling.

### Evidence Tools

| Tool | Input | Returns |
|------|-------|---------|
| `get_route_analysis` | trip_id | Extra distance %, deviation category, stops, traffic exception |
| `get_chat_log` | trip_id | Messages with sentiment, threat flags, contact dynamics |
| `get_fare_breakdown` | trip_id | Component validation, anomalies, overcharge amount |
| `get_user_history` | user_id | Disputes, rating, risk indicators, recurring pattern |
| `get_policy` | dispute_type | Relevant sections + citeable sub-clauses |

### Ruling Output

The Judge produces a structured ruling with:
- **Decision**: refund / compensation / no action
- **Amount**: dollar figure for the remedy
- **Confidence score**: 0.0–1.0 (below 0.6 flags for human review per Section 3.2)
- **Dual explanations**: separate natural-language reasoning for the rider and driver
- **Policy applied**: list of specific clauses cited in the ruling
- **Verification notes**: what the judge independently verified

---

## License

Built for the Tencent Cloud AI Singapore Hackathon 2026.
