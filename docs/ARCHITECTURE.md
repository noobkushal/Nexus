# NEXUS AI — System Architecture

NEXUS is a modular, local-first, multi-agent personal AI automation platform engineered for high agency, deterministic execution safety, and complete operational autonomy.

## Core Architectural Principles

1. **Provider-Independent AI Architecture**:
   - The application does NOT depend on any external AI API, cloud service, or local model runner for startup or baseline operation.
   - Built around an abstract `BaseLLMProvider` interface.
   - Default foundation provider is `MockProvider` (deterministic, instant, offline-safe, zero resource usage).
   - Future providers (Ollama, OpenAI-compatible APIs, Anthropic) connect via standard interface plugins without touching application core logic.

2. **Standalone & Lightweight**:
   - Starts and runs on local Windows systems with low resource footprints (e.g. RTX 3050 4GB VRAM, 16GB RAM).
   - Starts without PostgreSQL (graceful SQLite in-memory fallback).
   - Starts without n8n (built-in workflow simulation bridge).
   - No background heavy processes or blocking LLM loops during startup.

3. **Deterministic Safety & Security Barriers**:
   - Consequential external actions (sending emails, publishing content, deleting files, running unreviewed code) strictly require human approval.
   - Filesystem tool operations are sandboxed within approved storage directories. Path traversal outside authorized roots raises `SecurityViolationError`.
   - Conversational outputs are segregated from executed actions: NEXUS never claims an action was performed merely because an AI model suggested it.
   - Agents operate under least-privilege boundaries and cannot grant themselves additional permissions.

4. **Multi-Agent Specialization**:
   - **Aura (Personal Agent)**: Conversational interaction, daily briefings, task routing.
   - **Scout (Research Agent)**: Document synthesis and web research.
   - **Forge (Coding Agent)**: Workspaces, automated tests, mandatory Git checkpoints before modifications.
   - **Conduit (Workflow Agent)**: Triggering and monitoring n8n automation pipelines.
   - **Apex (Career Agent)**: Resume tailoring and human-reviewed LinkedIn outreach.

## System Topology

```
+-------------------------------------------------------------------------+
|                    Next.js Modern Dark Dashboard                        |
|   /dashboard, /chat, /agents, /tasks, /workflows, /memory, /projects,   |
|   /career, /settings (TypeScript, Tailwind CSS, Lucide Icons)           |
+------------------------------------+------------------------------------+
                                     | HTTP / REST (127.0.0.1:8000)
+------------------------------------v------------------------------------+
|                             FastAPI Backend                             |
|  +-------------------------------------------------------------------+  |
|  | API Routes: /health, /chat, /tasks, /agents, /workflows, /memory  |  |
|  +-------------------------------------------------------------------+  |
|  | AI Provider Abstraction Layer:                                    |  |
|  |   - BaseLLMProvider Interface                                     |  |
|  |   - ProviderRegistry (Active: Deterministic Mock Engine)          |  |
|  |   - (Optional future: OllamaProvider, OpenAIProvider)             |  |
|  +-------------------------------------------------------------------+  |
|  | Multi-Agent Orchestration:                                        |  |
|  |   - Aura, Scout, Forge, Conduit, Apex                             |  |
|  |   - Human-in-the-loop approval barriers                           |  |
|  |   - Structured activity logging & audit trail                     |  |
|  +-------------------------------------------------------------------+  |
|  | Sandboxed Filesystem Tools (Restricted to E:\NEXUS\storage)       |  |
|  +-------------------------------------------------------------------+  |
|  | Storage & Memory:                                                 |  |
|  |   - SQLite In-Memory fallback (Active)                            |  |
|  |   - Optional PostgreSQL + pgvector adapter                        |  |
+-------------------------------------------------------------------------+
```

## Directory Structure

```
E:\NEXUS
├── backend
│   ├── app
│   │   ├── agents           # Agent orchestrators & personas
│   │   ├── api              # Modular route handlers (health, chat, tasks...)
│   │   ├── core             # Centralized settings & structured logging
│   │   ├── memory           # Persistence & memory abstractions
│   │   ├── providers        # Provider-independent AI interface & mock engine
│   │   ├── schemas          # Typed Pydantic request/response models
│   │   ├── services         # Chat, task, and workflow domain services
│   │   ├── tools            # Sandboxed filesystem & utility tools
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI application entry point
│   ├── tests                # Automated pytest suite
│   ├── .env.example
│   ├── .env
│   └── requirements.txt
├── frontend                 # Next.js 14 App Router dashboard
│   ├── src
│   │   ├── app              # 9 dashboard route pages
│   │   └── components       # Sidebar, Header, UI controls
│   ├── package.json
│   └── tailwind.config.ts
├── docs                     # Documentation, guides & API references
├── storage                  # Sandboxed user storage
├── workflows                # Automation pipeline definitions
├── docker-compose.yml       # Optional infrastructure containers
└── README.md
```
