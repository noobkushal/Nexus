# NEXUS AI — Personal AI Operating System

NEXUS is a modular, local-first, multi-agent personal AI automation platform engineered for digital activities, task execution, coding, research, and communication workflows.

## Key Principles & Operational Capabilities
- **100% Dependency-Independent**: Starts and operates completely offline without Ollama, PostgreSQL, or n8n.
- **Provider-Independent AI Architecture**: Built on a modular provider interface (`BaseLLMProvider`) with an instant, deterministic mock provider active by default. Optional Ollama connection (`qwen3.5:4b`) available for non-blocking local inference.
- **Multi-Agent Roster**: Defined personas (Aura, Scout, Forge, Conduit, Apex) with strict capability scopes and least-privilege permission barriers.
- **Sandboxed Security & Safety Barriers**: Filesystem mutations are strictly quarantined within approved storage roots; consequential operations (emails, messages, pipeline triggers, deletions) require human approval before execution.
- **Web Research & Browser Retrieval**: Anti-SSRF URL validator and untrusted HTML sanitizer archiving research dossiers into `storage/documents/`.
- **Communications Hub**: Outbound email drafting, messaging (LinkedIn, Slack), and calendar scheduling with mandatory approval enforcement before transmission.
- **Executive Daily Briefings**: Automated operational summaries and scheduled reminders compiling tasks, health, and pending approvals into `storage/generated/`.
- **Modern Next.js Dashboard**: Dark aesthetic with deep charcoal backgrounds, responsive sidebar navigation, and 9 dedicated operating views.
- **Robust Test Suite**: 40 automated pytest tests passing with 100% success rate.

---

## Repository Structure

```
E:\NEXUS
├── backend
│   ├── app
│   │   ├── agents           # Agent personas & multi-agent orchestrator
│   │   ├── api              # REST routes (health, chat, tasks, agents, workflows, memory, settings)
│   │   ├── core             # Configuration (pydantic-settings) & structured logging
│   │   ├── memory           # Persistence layer with SQLite/in-memory fallback
│   │   ├── providers        # AI provider interface & deterministic mock engine
│   │   ├── schemas          # Typed Pydantic request/response models
│   │   ├── services         # Domain logic (chat service, task service, workflow service)
│   │   ├── tools            # Sandboxed filesystem & permission enforcement
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI application entry point
│   ├── tests                # Automated pytest suite (12 tests)
│   ├── .env.example
│   ├── .env
│   └── requirements.txt
├── frontend                 # Next.js 14 + Tailwind CSS dashboard
│   ├── src
│   │   ├── app              # 9 pages: /dashboard, /chat, /agents, /tasks, /workflows...
│   │   └── components       # Sidebar, Header, UI controls
│   ├── package.json
│   └── tailwind.config.ts
├── docs
│   ├── ARCHITECTURE.md      # Detailed system topology and security boundaries
│   ├── ROADMAP.md           # Multi-phase project delivery plan
│   ├── SETUP_WINDOWS.md     # Step-by-step PowerShell setup commands
│   └── API.md               # Complete REST API reference
├── storage                  # Sandboxed local storage
├── docker-compose.yml       # Optional infrastructure containers (Postgres, n8n)
└── README.md
```

---

## Quick Start (Windows PowerShell)

### 1. Launch the Backend Server
```powershell
cd E:\NEXUS\backend
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Backend API will be live at:
- **API Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Run the Backend Automated Tests
```powershell
cd E:\NEXUS\backend
.\.venv\Scripts\pytest.exe -v
```

### 3. Launch the Next.js Frontend Dashboard
In a second PowerShell window:
```powershell
cd E:\NEXUS\frontend
npm.cmd run dev
```
Open your browser to:
- **Mission Control Dashboard**: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
- **Chat Assistant**: [http://localhost:3000/chat](http://localhost:3000/chat)
- **Agents Roster**: [http://localhost:3000/agents](http://localhost:3000/agents)
- **Tasks & Work Items**: [http://localhost:3000/tasks](http://localhost:3000/tasks)
- **Workflows (n8n Bridge)**: [http://localhost:3000/workflows](http://localhost:3000/workflows)
- **Memory & Profile**: [http://localhost:3000/memory](http://localhost:3000/memory)
- **Coding Projects**: [http://localhost:3000/projects](http://localhost:3000/projects)
- **Career & Outreach**: [http://localhost:3000/career](http://localhost:3000/career)
- **System Settings**: [http://localhost:3000/settings](http://localhost:3000/settings)

---

## Documentation Links
- [System Architecture](file:///E:/NEXUS/docs/ARCHITECTURE.md)
- [Development Roadmap](file:///E:/NEXUS/docs/ROADMAP.md)
- [Windows Setup Guide](file:///E:/NEXUS/docs/SETUP_WINDOWS.md)
- [REST API Reference](file:///E:/NEXUS/docs/API.md)
