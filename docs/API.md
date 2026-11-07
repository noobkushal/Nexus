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

---

## 2. Chat & Multi-Agent State Graph

### `POST /api/v1/chat`
Sends a prompt message through the directed state graph (intent classification &rarr; agent routing &rarr; safety guard &rarr; response synthesis).

**Request Body:**
```json
{
  "message": "Can you check git code and run a test?",
  "conversation_id": "optional-uuid-string",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "[MOCK RESPONSE] Received prompt...",
  "conversation_id": "2f6b6148-6e63-41f3-8775-bfdc681e6b16",
  "provider": "mock",
  "model": "nexus-mock-engine-v1",
  "is_mock": true,
  "claimed_actions_executed": false,
  "intent": "coding",
  "routed_agent": "coding_agent",
  "requires_approval": false,
  "steps": [
    "Intent Classification -> 'coding'",
    "Graph Router -> Assigned to Agent 'Forge' (coding_agent)",
    "Safety Guard -> Read-only / Non-consequential query (Autonomous execution permitted)",
    "Synthesis -> Completed via Provider 'mock'"
  ]
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

---

## 6. Sandboxed Storage & Git Checkpoints

### `GET /api/v1/storage/compartments`
Lists approved storage compartments (`profile`, `documents`, `media`, `projects`, `generated`, `attachments`).

### `GET /api/v1/storage/files`
Lists files inside approved storage directories with size and timestamp metadata. Query parameter: `compartment` (`documents`, etc.).

### `GET /api/v1/storage/read`
Reads text content of a file within the sandbox. Query parameter: `path`. Returns 403 Forbidden on path traversal escape attempts.

### `POST /api/v1/storage/write`
Writes content to a sandboxed file within approved directory boundaries.

### `DELETE /api/v1/storage/delete`
Safely deletes a sandboxed file.

### `GET /api/v1/storage/git/status`
Returns live branch, current commit hash, and uncommitted modification count.

### `GET /api/v1/storage/git/checkpoints`
Lists recent Git commit snapshots. Query parameter: `limit`.

### `POST /api/v1/storage/git/checkpoint`
Creates an automated Git safety commit snapshot before consequential edits.

---

## 7. Workflows & Automation (n8n Bridge)

### `GET /api/v1/workflows`
Lists registered automated pipelines.

### `POST /api/v1/workflows/{workflow_id}/trigger`
Triggers an automation workflow (simulated in offline standalone mode).

### `GET /api/v1/workflows/executions`
Returns execution log and status history.

---

## 8. Long-Term Memory

### `GET /api/v1/memory`
Lists memory records. Query parameter: `category` (`profile`, `preferences`, `system`).

### `POST /api/v1/memory`
Stores a new memory record.

---

## 9. System Settings

### `GET /api/v1/settings`
Returns runtime configuration summary, active providers, and storage roots.

### `POST /api/v1/settings/provider`
Switches the active default provider.
