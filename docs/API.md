# NEXUS AI — REST API Documentation

Base URL: `http://127.0.0.1:8000`

Interactive OpenAPI Documentation:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 1. System Health & Core

### `GET /health` & `GET /api/v1/health`
Returns system status, active provider, persistence mode, and dependency readiness.

### `GET /model-status` & `GET /api/v1/model-status`
Non-blocking inspection of optional local Ollama connectivity and target model presence (`qwen3.5:4b`).

**Response:**
```json
{
  "target_model": "qwen3.5:4b",
  "ollama_base_url": "http://127.0.0.1:11434",
  "connectivity": {
    "connected": true,
    "target_model": "qwen3.5:4b",
    "model_available": true,
    "installed_models": ["qwen3.5:4b"]
  },
  "active_system_provider": "mock",
  "note": "NEXUS foundation is independent of Ollama; this endpoint is for optional local hardware diagnostic."
}
```

**Response:**
```json
{
  "status": "operational",
  "service": "NEXUS AI Backend",
  "environment": "development",
  "timestamp": "2026-11-07T14:00:00Z",
  "ai_provider": {
    "name": "mock",
    "is_mock": true,
    "is_available": true,
    "details": {
      "model": "nexus-mock-engine-v1",
      "mode": "deterministic_mock"
    }
  },
  "database": {
    "type": "sqlite_in_memory",
    "is_available": true
  },
  "automation": {
    "n8n_connected": false,
    "mode": "standalone_interface"
  },
  "dependencies": {
    "ollama_required": false,
    "external_apis_required": false,
    "postgres_required": false,
    "n8n_required": false
  }
}
```

---

## 2. Chat & Interaction

### `POST /api/v1/chat`
Sends a prompt message to the active provider and returns a validated, deterministic response.

**Request Body:**
```json
{
  "message": "Check system status",
  "conversation_id": "optional-uuid-string",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "[MOCK RESPONSE — NEXUS Foundation]\nSystem Status: Operational...",
  "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "provider": "mock",
  "model": "nexus-mock-engine-v1",
  "is_mock": true,
  "claimed_actions_executed": false,
  "timestamp": "2026-11-07T14:00:00Z",
  "metadata": {
    "tokens_used": 34,
    "history_length": 3
  }
}
```

### `GET /api/v1/chat/{conversation_id}`
Retrieves full conversation history for a given conversation.

---

## 3. Tasks Management

### `GET /api/v1/tasks`
Lists all tasks. Query parameters: `status` (`pending`, `in_progress`, `completed`, `failed`), `priority` (`low`, `medium`, `high`, `critical`).

### `POST /api/v1/tasks`
Creates a new task.

**Request Body:**
```json
{
  "title": "Review codebase security boundaries",
  "description": "Verify sandboxed filesystem checks",
  "priority": "high",
  "assigned_agent": "coding_agent"
}
```

### `PATCH /api/v1/tasks/{task_id}`
Updates task status or priority.

### `DELETE /api/v1/tasks/{task_id}`
Deletes a task by ID.

---

## 4. Multi-Agent Roster

### `GET /api/v1/agents`
Lists registered agents: Aura (Personal Assistant), Scout (Researcher), Forge (Developer), Conduit (Workflow), Apex (Career).

### `GET /api/v1/agents/{agent_id}`
Retrieves specific agent capabilities, approval barriers, and permissions.

### `GET /api/v1/agents/activities`
Returns audit log trail of recent agent operations.

---

## 5. Human-in-the-Loop Action Approvals

### `GET /api/v1/approvals`
Lists consequential action proposals submitted by agents requiring human approval. Query parameter: `status` (`pending`, `approved`, `rejected`).

### `POST /api/v1/approvals`
Submits an action proposal from an agent into the review queue.

### `POST /api/v1/approvals/{approval_id}/decision`
Submits human reviewer decision (`approved` or `rejected`) with audit notes.

**Request Body:**
```json
{
  "decision": "approved",
  "reviewer_notes": "Reviewed and verified safety boundary"
}
```

---

## 5. Workflows & Automation (n8n Bridge)

### `GET /api/v1/workflows`
Lists registered automated pipelines.

### `POST /api/v1/workflows/{workflow_id}/trigger`
Triggers an automation workflow (simulated in offline standalone mode).

### `GET /api/v1/workflows/executions`
Returns execution log and status history.

---

## 6. Long-Term Memory

### `GET /api/v1/memory`
Lists memory records. Query parameter: `category` (`profile`, `preferences`, `system`).

### `POST /api/v1/memory`
Stores a new memory record.

**Request Body:**
```json
{
  "category": "preferences",
  "key": "editor",
  "content": "Prefers dark themes with high information density",
  "importance": 2
}
```

---

## 7. System Settings

### `GET /api/v1/settings`
Returns runtime configuration summary, active providers, and storage roots.

### `POST /api/v1/settings/provider`
Switches the active default provider.
