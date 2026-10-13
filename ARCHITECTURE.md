# Ryde Dispute Resolver — Architecture Overview

A multi-agent autonomous dispute resolution system for the Ryde ride-hailing platform.
Three LLM-powered agents — **Rider Advocate**, **Driver Advocate**, and **Judge** —
collaborate to resolve rider-driver disputes by gathering evidence, arguing their case
against company policy, and issuing a binding ruling.

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Language | **Python 3.11+** | Rich agent/LLM ecosystem, fast prototyping |
| Agent framework | **LangGraph** | First-class multi-agent state graphs, built-in message passing, observable intermediate state, easy parallel-then-join flows |
| LLM provider | **Tencent Cloud Hunyuan** (OpenAI-compatible API) | Fits the Tencent Cloud AI Hackathon theme; wrapper is OpenAI-compatible so any provider can drop in |
| UI | **Streamlit** | Rapid UI for hackathons; native support for live-updating logs, structured data tables, and markdown rendering |
| Data format | **JSON** (structured evidence) | Easy to author sample disputes; no DB needed for MVP |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI (app/)                       │
│  Dispute form · Evidence panel · Live message log · Ruling panel  │
└──────────────┬──────────────────────────────────┬───────────────┘
               │ submit dispute                    │ render
               ▼                                   ▲
┌──────────────────────────────────────────────────┐│
│              LangGraph Orchestrator (graph/)     ││
│                                                   ││
│   ┌─────────────┐         ┌──────────────────┐   ││
│   │ Rider        │         │ Driver Advocate  │   ││
│   │ Advocate     │  ╱╲     │                  │   ││
│   │ (pro-rider)  │ ╱  ╲    │ (pro-driver)     │   ││
│   └──────┬───────┘╱    ╲   └────────┬─────────┘   ││
│          │ arguments  ╲   ╲          │             ││
│          ▼             ╲   ╲         ▼             ││
│   ┌──────────────────────────────────────────────┐ ││
│   │              Judge Agent                     │ ││
│   │  weighs both cases · applies policy · rules  │ ││
│   └──────────────────┬───────────────────────────┘ ││
│                      │ ruling                        ││
│                      ▼                               ││
│               [Output: Ruling + Explanation]          ││
│                                                       │
│   ══════ Shared State (graph/state.py) ══════       │
│   dispute · evidence · rider_arg · driver_arg ·      │
│   ruling · message_log[]                             │
└──────────────────────────────────────────────────────┘│
               │ evidence queries                        │
               ▼                                        │
┌──────────────────────────────────────────────────────┐│
│              Evidence Layer (evidence/)              ││
│  GPS route · Chat logs · Fare breakdown · History    ││
└──────────────────────────────────────────────────────┘│
               │ policy lookup                           │
               ▼                                        │
┌──────────────────────────────────────────────────────┐│
│           Policy Knowledge (data/policies/)          ││
│  ryde_policy.md — route deviation, no-show, refunds   ││
└──────────────────────────────────────────────────────┘
```

---

## Data Flow (step by step)

1. **Dispute submission** — User selects a dispute type (route deviation / no-show)
   and a sample case (or fills a form). The dispute record (`Dispute` model) enters
   the graph as initial state.

2. **Evidence loading** — The `load_evidence` node pulls all structured data tied to
   the `ride_id`: GPS route points, chat logs, fare breakdown, rider history, driver
   history. Stored in `state.evidence`.

3. **Parallel advocate phase** — `Rider Advocate` and `Driver Advocate` run
   concurrently (LangGraph parallel branches). Each advocate:
   - Receives the full evidence set.
   - Calls evidence tools to extract the facts favorable to its side.
   - Queries the policy document for relevant clauses.
   - Produces a structured `Argument`: claim, evidence references, policy citations,
     requested remedy.
   - Streams every intermediate thought/tool-call to `state.message_log`.

4. **Judge phase** — Once both advocates complete (LangGraph join), the `Judge` agent:
   - Reads both arguments + the raw evidence.
   - Independently verifies key facts (e.g., actual GPS deviation distance).
   - Applies policy rules to determine fault.
   - Outputs a `Ruling`: decision (`refund` / `compensation` / `no_action`),
     recommended action, amount, confidence score (0.0–1.0), and a natural-language
     explanation addressed to both rider and driver.

5. **Render** — Streamlit displays the ruling card, the full evidence (GPS map, chat
   transcript, fare table), and the chronological message log showing every inter-agent
   communication.

---

## The Three Agents

### 1. Rider Advocate (`agents/rider_advocate.py`)

- **Role**: Argues the rider's case. Pro-rider bias by design.
- **Inputs**: full evidence, policy doc, dispute type.
- **Tools**: `query_gps`, `query_chat`, `query_fare`, `query_history`, `query_policy`.
- **Output**: `Argument` — claim summary, list of evidence references (with reasoning),
  policy citations, requested remedy (e.g., "full refund of $12.50").
- **Logging**: Every tool call and reasoning step appended to `message_log`.

### 2. Driver Advocate (`agents/driver_advocate.py`)

- **Role**: Argues the driver's case. Pro-driver bias by design.
- **Inputs**: same as rider advocate.
- **Tools**: same toolset.
- **Output**: `Argument` — same structure, pro-driver framing.
- **Logging**: Same as above.

### 3. Judge (`agents/judge.py`)

- **Role**: Neutral arbiter. Weighs both arguments against policy and raw evidence.
- **Inputs**: both advocates' arguments + raw evidence + policy doc.
- **Output**: `Ruling` —
  - `decision`: `"refund" | "compensation" | "no_action"`
  - `recommended_action`: short description (e.g., "Refund $8.00 to rider")
  - `amount`: float (0.0 if no_action)
  - `confidence`: float 0.0–1.0
  - `explanation_rider`: natural-language explanation for the rider
  - `explanation_driver`: natural-language explanation for the driver
  - `policy_basis`: list of policy clauses applied
- **Logging**: Judge's reasoning and ruling logged to `message_log`.

---

## LangGraph State Schema (`graph/state.py`)

```python
from typing import TypedDict, Literal
from models.dispute   import Dispute
from models.evidence  import Evidence
from models.argument  import Argument
from models.ruling    import Ruling
from models.message   import AgentMessage

class DisputeState(TypedDict):
    dispute: Dispute                       # input dispute record
    evidence: Evidence                     # loaded structured data
    rider_argument: Argument | None        # rider advocate output
    driver_argument: Argument | None       # driver advocate output
    ruling: Ruling | None                  # judge output
    message_log: list[AgentMessage]        # every inter-agent message
    phase: Literal["init", "advocates", "judge", "done"]
```

---

## Message Log Model (`models/message.py`)

Every message between agents is a structured record, not free text:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class AgentMessage(BaseModel):
    timestamp: datetime
    sender:    Literal["rider_advocate", "driver_advocate", "judge", "system"]
    recipient: Literal["rider_advocate", "driver_advocate", "judge", "all"]
    msg_type:  Literal["evidence_query", "policy_query", "argument", "ruling",
                       "reasoning", "tool_result"]
    content:   str                        # the message body
    metadata:  dict = Field(default_factory=dict)
    # metadata can hold: evidence_ref, policy_clause, tool_name, tool_args, etc.
```

The UI renders `message_log` as a chronological timeline — each entry shows sender,
recipient, type badge, content, and expandable metadata. This satisfies the
"inter-agent communication must be observable" requirement.

---

## Dispute Types

### Route Deviation

A rider claims the driver took a longer route, inflating the fare. Evidence includes
GPS waypoints (expected vs. actual), fare breakdown (distance charge), and chat logs
(if the driver explained the detour). Policy clause: "Drivers must follow the
navigation-recommended route unless rider agrees to a deviation."

### No-Show Charge

A rider was charged a no-show fee. The rider claims they were at the pickup point on
time; the driver claims they waited the full window. Evidence includes GPS timestamps
at pickup, chat logs, and the no-show charge on the fare breakdown. Policy clause:
"No-show fee applies if rider is not at pickup 5 min after arrival; driver must attempt
contact."

---

## Project Folder Structure

```
ryde-dispute-resolver/
├── README.md
├── ARCHITECTURE.md                  ← this file
├── requirements.txt
├── .env.example                     # API keys, model name
├── run.py                           # entry point → streamlit run
│
├── app/                             # Streamlit UI
│   ├── __init__.py
│   ├── ui.py                        # main page: dispute form → run → results
│   └── components/
│       ├── dispute_form.py          # dispute type selector + sample picker
│       ├── evidence_panel.py        # GPS map, chat transcript, fare table
│       ├── message_log.py           # inter-agent message timeline renderer
│       └── ruling_panel.py          # ruling card: decision, amount, confidence
│
├── agents/                          # the three LLM agents
│   ├── __init__.py
│   ├── base.py                      # BaseAgent: LLM wrapper, tool registration,
│   │                                #   message logging, prompt scaffolding
│   ├── rider_advocate.py            # Rider Advocate node
│   ├── driver_advocate.py           # Driver Advocate node
│   └── judge.py                     # Judge node
│
├── graph/                           # LangGraph orchestration
│   ├── __init__.py
│   ├── orchestrator.py              # build the StateGraph: nodes, edges,
│   │                                #   parallel branches, join, conditional flow
│   ├── state.py                     # DisputeState TypedDict (shared state schema)
│   └── tools.py                     # evidence/policy tool functions exposed to agents
│
├── evidence/                        # evidence loaders & analyzers
│   ├── __init__.py
│   ├── loaders.py                   # load GPS, chat, fare, history from JSON
│   ├── gps.py                       # route deviation detection, distance calc
│   ├── chat.py                      # chat log summarization / key-extraction
│   ├── fare.py                      # fare breakdown analysis
│   └── history.py                   # rider/driver dispute history & ratings
│
├── models/                          # Pydantic data models
│   ├── __init__.py
│   ├── dispute.py                   # Dispute
│   ├── evidence.py                  # Evidence (GPS, Chat, Fare, History)
│   ├── argument.py                  # Argument (advocate output)
│   ├── ruling.py                    # Ruling (judge output)
│   └── message.py                   # AgentMessage (log entry)
│
├── llm/                             # LLM client
│   ├── __init__.py
│   └── client.py                    # OpenAI-compatible wrapper (Tencent Hunyuan
│                                  #   default; swappable)
│
├── data/                            # sample data & policy
│   ├── policies/
│   │   └── ryde_policy.md           # company policy: route deviation, no-show,
│   │                                #   refund rules, compensation tiers
│   ├── samples/
│   │   ├── route_deviation_case.json  # sample dispute: GPS + fare + chat
│   │   └── no_show_case.json          # sample dispute: no-show charge
│   └── templates/
│       └── dispute_schema.json      # blank dispute template
│
├── config/
│   ├── __init__.py
│   └── settings.py                  # API keys, model name, thresholds, paths
│
└── tests/
    ├── __init__.py
    ├── test_route_deviation.py      # end-to-end on route deviation sample
    ├── test_no_show.py              # end-to-end on no-show sample
    └── test_message_log.py          # verify all messages are logged
```

---

## Key Design Decisions

1. **LangGraph over CrewAI** — LangGraph's explicit state graph gives us full control
   over the parallel-advocates → join → judge flow, and every state transition is
   inspectable. The shared `message_log` in state is the single source of truth for
   observable communication.

2. **Advocates run in parallel** — They don't depend on each other (each reviews the
   same evidence independently). LangGraph's fan-out → join pattern handles this
   naturally and reduces latency.

3. **Structured message log, not free chat** — Messages are typed
   (`evidence_query`, `policy_query`, `argument`, `ruling`, `reasoning`,
   `tool_result`) with metadata. This makes the UI timeline rich and filterable,
   and the log itself becomes an auditable artifact.

4. **Policy as a markdown document** — The policy is a plain `.md` file. Agents query
   it via a `query_policy` tool (simple keyword/section search). This is hackathon-
   friendly: edit the policy, re-run, no vector DB needed. Could upgrade to RAG later.

5. **OpenAI-compatible LLM client** — The `llm/client.py` wrapper speaks the
   OpenAI API format. Tencent Cloud Hunyuan exposes an OpenAI-compatible endpoint,
   so switching providers is a one-line config change.

6. **Streamlit for speed** — A single-page Streamlit app handles the dispute form,
   the live message log (auto-refresh during graph execution), evidence display, and
   the ruling card. No build step, deploys to Tencent Cloud in minutes.
