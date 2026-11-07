# NEXUS AI — Windows Setup & Execution Guide

This guide provides step-by-step Windows PowerShell instructions to set up, run, and test the NEXUS AI platform in standalone foundation mode.

## Hardware & Environment Overview
- **OS**: Windows 10/11 64-bit
- **Shell**: Windows PowerShell (or PowerShell 7+)
- **Python**: Python 3.10+ (tested with 3.15)
- **Node.js**: v18+ (tested with v26 LTS / npm 11+)
- **Resource Constraints**: RTX 3050 (4 GB VRAM), 16 GB RAM.
- **External Dependencies**: NONE. The foundation operates with zero external dependencies (no Ollama, PostgreSQL, or n8n required).

---

## 1. Quick Launch Scripts (One-Click Helpers)

Pre-built PowerShell scripts are available in `scripts/`:

### Full System Verification (Backend Pytest + Next.js Production Build)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify-all.ps1
```

### Launch FastAPI Backend
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-backend.ps1
```

### Launch Next.js Frontend
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-frontend.ps1
```

### Run Automated Tests
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-tests.ps1
```

---

## 2. Manual Backend Setup & Startup

### Step 1.1: Navigate to Backend Directory
Open Windows PowerShell and navigate to the backend folder:
```powershell
cd E:\NEXUS\backend
```

### Step 1.2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(Note: If PowerShell complains about script execution policy, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` or invoke the python executable directly using `.\.venv\Scripts\python.exe`)*

### Step 1.3: Install Dependencies
```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### Step 1.4: Run the Automated Pytest Suite
Run the test suite to verify all APIs, mock providers, and security barriers:
```powershell
.\.venv\Scripts\pytest.exe -v
```

### Step 1.5: Launch the FastAPI Backend Server
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Once running, verify backend endpoints:
- Root API: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Interactive Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 2. Frontend Setup & Startup

### Step 2.1: Navigate to Frontend Directory
Open a second Windows PowerShell terminal:
```powershell
cd E:\NEXUS\frontend
```

### Step 2.2: Install NPM Dependencies
Use `npm.cmd` on Windows:
```powershell
npm.cmd install
```

### Step 2.3: Build Production Bundle (Optional Verification)
```powershell
npm.cmd run build
```

### Step 2.4: Start Next.js Development Server
```powershell
npm.cmd run dev
```
Open your browser to:
- Mission Control Dashboard: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
- Conversational Chat: [http://localhost:3000/chat](http://localhost:3000/chat)
- Multi-Agent Roster: [http://localhost:3000/agents](http://localhost:3000/agents)
- Tasks Management: [http://localhost:3000/tasks](http://localhost:3000/tasks)
- Automation Workflows: [http://localhost:3000/workflows](http://localhost:3000/workflows)
- Long-Term Memory: [http://localhost:3000/memory](http://localhost:3000/memory)
- Coding Projects: [http://localhost:3000/projects](http://localhost:3000/projects)
- Career & Outreach: [http://localhost:3000/career](http://localhost:3000/career)
- System Settings: [http://localhost:3000/settings](http://localhost:3000/settings)

---

## 3. Quick Verification Script (PowerShell One-Liner)

To verify the running backend without opening a browser:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" | ConvertTo-Json -Depth 4
```
Expected output:
```json
{
  "status": "operational",
  "service": "NEXUS AI Backend",
  "ai_provider": {
    "name": "mock",
    "is_mock": true,
    "is_available": true
  },
  "dependencies": {
    "ollama_required": false,
    "postgres_required": false
  }
}
```

To test the chat endpoint:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/chat" -Method Post -ContentType "application/json" -Body '{"message": "Status report"}' | ConvertTo-Json
```
