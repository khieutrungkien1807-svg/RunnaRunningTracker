# Antigravity Super-System: Architecture 6.0.0 (Solid-State)

## 1. Executive Summary
Antigravity Orchestrator is a production-hardened, deterministic multi-agent orchestration engine. It operates on a **Brain-Body-Reflex-Memory** architecture, designed to eliminate LLM hallucination through strict schema boundaries, hard deterministic checks, and actionable blueprint injection.

## 2. Core Components

| Module | Component | Responsibility | Tech Stack |
|--------|-----------|----------------|------------|
| **Neocortex** | `Planner` | Synthesizes objectives into a multi-step execution plan with rigid parameters and clear success criteria. | LLM + Instructor (Pydantic) |
| **Motor Cortex** | `ActionRunner` | Executes file I/O operations and shell commands safely within sandboxed boundaries. | Python Subprocesses, OS Modules |
| **Cerebellum** | `Checker` | Performs deterministic Level-1 verification to ground the system's completed tasks to absolute reality. | OS Native Checks |
| **Hippocampus**| `SkillStore` | Retrieves proven, programmable blueprints (macros) based on error patterns or intent, forcing the Planner to follow a verified script. | FAISS / Graph / JSON |

## 3. High-Level Flow (Mermaid)

```mermaid
flowchart TD
    %% Define Styles
    classDef user fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff
    classDef memory fill:#d946ef,stroke:#c026d3,stroke-width:2px,color:#fff
    classDef cortex fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff
    classDef motor fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    classDef check fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
    classDef repair fill:#ef4444,stroke:#dc2839,stroke-width:2px,color:#fff

    USER["👤 USER INPUT<br/>(e.g., 'Sửa lỗi is not defined ở App.js')"]:::user

    %% Memory
    STORE["🧠 SKILL STORE (Hippocampus)<br/>Hybrid Retrieval (Intent / Errors)"]:::memory
    BLUEPRINT["📜 Blueprint Template<br/>(Actionable Macro + Success Criteria)"]:::memory

    %% Neocortex
    PLANNER["🧩 PLANNER (Neocortex)<br/>Input: Task + Blueprint<br/>Output: ExecutionPlan"]:::cortex

    %% Motor Cortex
    subgraph ACTION EXECUTION LOOP (Motor Cortex)
        direction LR
        RUNNERS["Action Dispatcher"]:::motor
        IO1["read_file"]:::motor
        IO2["write_file"]:::motor
        IO3["generate_code"]:::motor
        IO4["run_cmd"]:::motor
        RUNNERS --> IO1 & IO2 & IO3 & IO4
    end

    %% Cerebellum
    CHECKER["⚖️ CHECKER (Cerebellum)<br/>- file_exists<br/>- file_contains<br/>- cmd_exit_zero"]:::check

    %% Repair Loop
    REPAIR["❤️‍🩹 REPLAN & REPAIR<br/>(Self-Healing Loop)"]:::repair
    STAGNATION{"Stagnation<br/>/ Max Tries?"}:::repair

    %% Flow
    USER --> STORE
    STORE -- Pattern Matched --> BLUEPRINT
    STORE -- No Match --> PLANNER
    BLUEPRINT -- Hard Override --> PLANNER
    PLANNER --> RUNNERS
    IO1 & IO2 & IO3 & IO4 --> CHECKER

    CHECKER -- [Errors] --> REPAIR
    CHECKER -- [Pass] --> SUCCESS((🏁 SUCCESS))

    REPAIR --> STAGNATION
    STAGNATION -- NO --> STORE
    STAGNATION -- YES --> HALT((🛑 HARD HALT))
```

## 4. Phase 3: Actionable Intelligence (Zero Hallucination)
The critical breakthrough of Antigravity is treating the RAG (Retrieval-Augmented Generation) mechanism not as a knowledge base, but as an **Execution Constraint Base**.

When the `SkillStore` detects a pattern (like an NPM missing dependency), it does not merely feed the LLM a document describing the fix. It directly injects an `ExecutionPlan` blueprint (e.g., *Action 1: Run NPM Install, Action 2: Check Exit Code*) and forces the Planner to instantiate this proven template. This fundamentally alters the architecture from an unconstrained generative loop into a **Surgical Execution System**.

## 5. Security & Verification Guardrails
- **Path Sandboxing**: The `ActionRunner` mathematically blocks execution traversing out of the defined workspace (`c:\Users\<YOUR_USERNAME>\.gemini\antigravity`).
- **Command Whitelisting**: Only deterministic command strings explicitly formatted are dispatched.
- **Ground Truth Grounding**: The system never asks the LLM "Did you finish this?". It asks the OS "Does this file exist and does `npm run build` exit code 0?".
