# Ryde Dispute Resolver — Architecture Overview

A multi-agent autonomous dispute resolution system for the Ryde ride-hailing platform.
Three LLM-powered agents — **Rider Advocate**, **Driver Advocate**, and **Judge** —
collaborate to resolve rider-driver disputes by gathering evidence, arguing their case
against company policy, countering the opposing argument, and issuing a binding ruling.

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Language | **Python 3.11+** | Rich agent/LLM ecosystem, fast prototyping |
| Agent framework | **LangGraph** | First-class multi-agent state graphs, built-in message passing, observable intermediate state, parallel-then-join diamond flows |
| LLM provider | **Tencent Cloud Hunyuan** (OpenAI-compatible API) | Fits the Tencent Cloud AI Hackathon theme; wrapper is OpenAI-compatible so any provider can drop in |
| UI | **Streamlit** | Rapid UI for hackathons; native support for live-updating logs, structured data tables, and markdown rendering |
| Map viz | **Folium + streamlit-folium** | Interactive leaflet maps for GPS route visualization |
| Data format | **JSON** (structured evidence) | Easy to author sample disputes; no DB needed for MVP |

---

## System Architecture

```
                         START
                           |
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐     ┌──────────▼──────────┐
     │  Rider Advocate  │     │  Driver Advocate    │
     │  (pro-rider)     │     │  (pro-driver)       │
     │  gathers evidence│     │  gathers evidence   │
     │  builds argument │     │  builds argument    │
     └────────┬─────────┘     └──────────┬──────────┘
              │                          │
              │   ┌──────────────────┐   │
              │   │  PHASE 2:        │   │
              └───┤  Rebuttal phase  ├───┘
                  │                  │
     ┌────────────▼──┐         ┌─────▼──────────────┐
     │ Rider Rebuttal│         │ Driver Rebuttal    │
     │ counters      │         │ counters           │
     │ driver's arg  │         │ rider's arg        │
     └────────┬──────┘         └──────┬─────────────┘
              │                       │
              └───────────┬───────────┘
                          │
                 ┌────────▼────────┐
                 │     Judge       │
                 │  weighs both    │
                 │  args + rebuttals│
                 │  applies policy │
                 │  issues ruling  │
                 └────────┬────────┘
                          │
                         END
```

---

## LangGraph Diamond Topology

The system uses a **diamond-shaped state graph** with three phases:

| Phase | Nodes | Pattern | Description |
|-------|-------|---------|-------------|
| 1 — Advocates | Rider Advocate + Driver Advocate | Parallel (fan-out) | Both advocates independently gather evidence and build structured arguments |
| 2 — Rebuttals | Rider Rebuttal + Driver Rebuttal | Parallel (fan-out) | Each advocate reviews the opponent's argument and produces counterpoints |
| 3 — Judge | Judge | Join + decide | Judge weighs both arguments + rebuttals, verifies key claims, issues ruling |

The parallel execution is handled natively by LangGraph's `StateGraph` — both advocate
nodes run concurrently from `START`, and both rebuttal nodes run concurrently after the
advocate phase completes. The judge node runs only after both rebuttals finish.

---

## Data Flow (step by step)

1. **Dispute submission** — User selects a dispute type (route deviation / no-show)
   and a sample case (or fills a form). The dispute record enters the graph as
   initial state.

2. **Phase 1 — Parallel advocate arguments** — `Rider Advocate` and `Driver Advocate`
   run concurrently. Each advocate:
   - Receives the full evidence set.
   - Calls evidence tools (`query_gps`, `query_chat`, `query_fare`, `query_history`,
     `query_policy`).
   - Produces a structured `Argument`: claim, evidence references, policy citations,
     requested remedy.
   - Streams every intermediate thought/tool-call to `state.message_log`.

3. **Phase 2 — Parallel rebuttals** — Each advocate sees the opponent's argument and
   produces a `Rebuttal`:
   - Counterpoints (2-4 specific points rebutting the opponent's key claims).
   - Revised claim, remedy, and amount (may differ from original).
   - Reasoning explaining why the opponent's case fails.
   - Logged as `rebuttal` msg_type in the message log.

4. **Phase 3 — Judge ruling** — The `Judge` agent:
   - Reads both arguments + both rebuttals + raw evidence.
   - Independently verifies key facts via tools (e.g., GPS deviation distance).
   - Applies policy rules to determine fault.
   - Outputs a `Ruling`: decision (`refund` / `compensation` / `no_action`),
     amount, confidence score (0.0–1.0), and dual natural-language explanations.

5. **Render** — Streamlit displays:
   - GPS route map (interactive folium map showing actual vs optimal route).
   - Evidence panel (chat transcript, fare table, user history).
   - Chronological message log showing every inter-agent communication.
   - Ruling card with decision, amount, confidence, and policy citations.
   - Advocate case summaries with rebuttal counterpoints.

---

## The Three Agents

### 1. Rider Advocate (`agents/rider_advocate.py`)

- **Role**: Argues the rider's case. Pro-rider bias by design.
- **Phase 1**: Gathers evidence, builds structured `Argument`.
- **Phase 2**: Reviews driver's argument, produces `Rebuttal` with counterpoints.
- **Tools**: `query_gps`, `query_chat`, `query_fare`, `query_history`, `query_policy`.
- **Prompts**: `agents/prompts/rider_advocate.md`, `agents/prompts/rider_rebuttal.md`.

### 2. Driver Advocate (`agents/driver_advocate.py`)

- **Role**: Argues the driver's case. Pro-driver bias by design.
- **Phase 1**: Gathers evidence, builds structured `Argument`.
- **Phase 2**: Reviews rider's argument, produces `Rebuttal` with counterpoints.
- **Tools**: same toolset.
- **Prompts**: `agents/prompts/driver_advocate.md`, `agents/prompts/driver_rebuttal.md`.

### 3. Judge (`agents/judge.py`)

- **Role**: Neutral arbiter. Weighs both arguments + rebuttals against policy.
- **Phase 3**: Reviews all arguments and rebuttals, verifies key claims, issues ruling.
- **Output**: `Ruling` with decision, amount, confidence, dual explanations.
- **Prompts**: `agents/prompts/judge.md`.

---

## LangGraph State Schema (`graph/state.py`)

```python
class DisputeState(TypedDict):
    case: CaseData                           # input dispute record
    llm: LLMClient                           # shared LLM client
    log: ConversationLog                     # shared message log
    rider_argument: Argument | None          # Phase 1 output
    driver_argument: Argument | None         # Phase 1 output
    rider_rebuttal: Rebuttal | None          # Phase 2 output
    driver_rebuttal: Rebuttal | None         # Phase 2 output
    ruling: Ruling | None                    # Phase 3 output
```

---

## Data Models

### Argument (`models/argument.py`)

```python
class Argument(BaseModel):
    agent: str                    # "rider_advocate" or "driver_advocate"
    claim: str                    # one-sentence summary
    evidence: list[EvidenceItem]  # cited evidence with source, fact, reference
    policy_cited: list[PolicyCitation]  # clause, title, relevance
    requested_remedy: str         # "refund", "compensation", "no_action"
    requested_amount: float
    reasoning: str
    tools_called: list[str]
```

### Rebuttal (`models/argument.py`)

```python
class Rebuttal(BaseModel):
    agent: str                     # "rider_advocate" or "driver_advocate"
    counterpoints: list[str]       # specific points rebutting opponent's argument
    revised_claim: str             # may differ from original
    revised_remedy: str            # may differ from original
    revised_amount: float
    reasoning: str
```

### Ruling (`models/ruling.py`)

```python
class Ruling(BaseModel):
    ruling: str              # "refund", "compensation", "no_action"
    action: str              # short description
    amount: float = 0.0
    confidence: float        # 0.0-1.0, below 0.6 flags for human review
    reasoning_for_rider: str
    reasoning_for_driver: str
    policy_applied: list[PolicyCitation]
    tools_called: list[str]
    verification_notes: str
```

---

## Message Log Model (`models/message.py`)

Every message between agents is a structured record, not free text:

```python
class AgentMessage(BaseModel):
    timestamp: datetime
    sender:    Literal["rider_advocate", "driver_advocate", "judge", "system"]
    recipient: Literal["rider_advocate", "driver_advocate", "judge", "all"]
    msg_type:  Literal[
        "tool_call", "tool_result", "reasoning",
        "argument", "rebuttal", "ruling", "system",
    ]
    content:   str
    metadata:  dict = Field(default_factory=dict)
```

The UI renders `message_log` as a chronological timeline — each entry shows sender,
recipient, type badge, content, and expandable metadata. The `rebuttal` type was added
in Phase 2 to distinguish counter-arguments from initial arguments.

---

## GPS Route Visualization (`app/components/route_map.py`)

When a route deviation case includes GPS waypoints, the evidence panel renders an
interactive folium map:

- **Red solid line** — actual route taken by the driver.
- **Green dashed line** — optimal/recommended route.
- **Blue marker** — pickup point.
- **Purple marker** — dropoff point.
- **Small dots** — individual waypoints with tooltip details.
- **Auto-fit bounds** — map zooms to contain both routes.

This lets judges and users visually assess the severity of any route deviation.

---

## Two Execution Modes

### Demo Mode (no API key needed)
- Rule-based mock arguments, rebuttals, and rulings.
- Calls real evidence tools for data analysis.
- Used for UI demos and testing.

### Live Mode (requires LLM API key)
- Full LangGraph state machine with real LLM calls.
- Agents use structured prompts to generate arguments and rebuttals.
- Judge independently verifies claims via tools.

Both modes follow the same diamond topology and return the same 5-tuple:
`(ruling, rider_argument, driver_argument, rider_rebuttal, driver_rebuttal)`.

---

## Project Folder Structure

```
ryde-dispute-resolver/
├── README.md
├── ARCHITECTURE.md                    <- this file
├── Dockerfile                         <- container deployment
├── docker-compose.yml                 <- one-command deploy
├── requirements.txt
├── .env.example                       # API keys, model name
├── run.py                             # entry point -> streamlit run
│
├── app/                               # Streamlit UI
│   ├── ui.py                          # main page: form -> run -> results
│   └── components/
│       ├── dispute_form.py            # dispute type selector + sample picker
│       ├── evidence_panel.py          # GPS map, chat, fare table
│       ├── route_map.py               # folium interactive route visualization
│       ├── message_log.py             # inter-agent message timeline
│       └── ruling_panel.py            # ruling card: decision, amount, confidence
│
├── agents/                            # the three LLM agents
│   ├── base.py                        # BaseAgent: LLM wrapper, tool registration
│   ├── rider_advocate.py              # Phase 1 + Phase 2 (rebuttal)
│   ├── driver_advocate.py             # Phase 1 + Phase 2 (rebuttal)
│   ├── judge.py                       # Phase 3 (ruling, with rebuttals)
│   └── prompts/
│       ├── rider_advocate.md
│       ├── rider_rebuttal.md
│       ├── driver_advocate.md
│       ├── driver_rebuttal.md
│       └── judge.md
│
├── graph/                             # LangGraph orchestration
│   ├── orchestrator.py                # demo mode + live mode entry points
│   ├── langgraph_orchestrator.py      # diamond StateGraph: parallel -> rebuttal -> judge
│   ├── state.py                       # DisputeState TypedDict
│   └── tools.py                       # evidence/policy tool functions
│
├── evidence/                          # evidence loaders & analyzers
│   ├── loaders.py                     # load cases from JSON
│   ├── gps.py                         # route deviation detection
│   ├── chat.py                        # chat log analysis
│   ├── fare.py                        # fare breakdown analysis
│   └── history.py                     # rider/driver dispute history
│
├── models/                            # Pydantic data models
│   ├── argument.py                    # Argument, Rebuttal, EvidenceItem, PolicyCitation
│   ├── ruling.py                      # Ruling
│   └── message.py                     # AgentMessage, ConversationLog
│
├── llm/                               # LLM client
│   └── client.py                      # OpenAI-compatible wrapper (Hunyuan default)
│
├── data/                              # sample data & policy
│   ├── policies/ryde_policy.md        # company policy document
│   └── samples/                       # 4 sample dispute cases
│       ├── route_deviation_clear.json
│       ├── route_deviation_borderline.json
│       ├── no_show_genuine.json
│       ├── no_show_disputed.json
│       └── index.json
│
├── config/settings.py                 # thresholds, paths, fare rates
│
└── tests/                             # unit tests (demo mode)
    ├── test_route_deviation.py        # route deviation cases
    ├── test_no_show.py                # no-show cases
    └── test_message_log.py           # message logging verification
```

---

## Key Design Decisions

1. **LangGraph diamond topology** — The parallel-advocates → parallel-rebuttals → judge
   flow gives us a true adversarial debate structure. Each advocate first builds their
   best case independently, then gets to rebut the opponent's argument before the judge
   rules. This mirrors real dispute resolution.

2. **Rebuttal phase** — Without rebuttals, the judge would only see each advocate's
   opening statement. The rebuttal phase ensures the judge sees counter-arguments,
   revised claims, and updated remedies — producing better-informed rulings.

3. **Structured message log, not free chat** — Messages are typed (`tool_call`,
   `tool_result`, `reasoning`, `argument`, `rebuttal`, `ruling`, `system`) with
   metadata. This makes the UI timeline rich and filterable, and the log itself
   becomes an auditable artifact.

4. **Policy as a markdown document** — The policy is a plain `.md` file. Agents query
   it via a `query_policy` tool (keyword/section search). Edit the policy, re-run —
   no vector DB needed.

5. **OpenAI-compatible LLM client** — The `llm/client.py` wrapper speaks the OpenAI
   API format. Tencent Cloud Hunyuan exposes an OpenAI-compatible endpoint, so
   switching providers is a one-line config change.

6. **GPS route visualization** — Interactive folium maps let judges and users visually
   compare the actual vs optimal route, making route deviation disputes immediately
   clear without parsing raw GPS coordinates.

7. **Demo mode + Live mode** — Demo mode runs the full pipeline with rule-based outputs
   (no API key), so the UI is always demonstrable. Live mode swaps in real LLM calls
   via the same LangGraph topology.
