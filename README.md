# 🧠 DebugIQ Backend

The backend for **DebugIQ**, an autonomous debugging and patching agent platform built using **FastAPI**, powered by **GPT-4o**, **Gemini**, and multi-agent orchestration.

This service is responsible for diagnosis, patch suggestion, QA validation, auto-documentation, pull request creation, and agent workflow orchestration.

---

## 🚀 Features

- 🤖 **Autonomous Multi-Step Workflows** (`run_autonomous_workflow.py`)
- 🧠 DebugIQ voice bi-directional + chat
  - Root cause analysis
  - Patch generation (diff + explanation)
  - QA validation + result interpretation
  - Auto-documentation and PR prep
- 🔗 GitHub PR creation (stubbed / production-ready)
- 📊 Agent & workflow metrics via `/metrics/status`
- 🗃️ Mock in-memory issue database (`scripts.mock_db`)
- 📦 Modular architecture — plug-and-play agents

---

## 🧱 Architecture

FastAPI
│
├── /app
│ └── api/
│ ├── autonomous_router.py # Orchestrated endpoints
│ ├── metrics_router.py # Agent metrics
│ ├── issues_router.py # Inbox / triage endpoints
│ ├── voice_ws_router.py # Voice (WebSocket)
│ └── voice_interactive_router.py # Voice (text/audio via Gemini)
│
├── /scripts
│ ├── run_autonomous_workflow.py # 🧠 Core agent pipeline
│ ├── platform_data_api.py # DB/metadata fetchers
│ ├── agent_suggest_patch.py # Patch LLM agent
│ ├── autonomous_diagnose_issue.py # Root cause agent
│ ├── validate_proposed_patch.py # QA validator
│ ├── create_fix_pull_request.py # PR creator
│ └── mock_db.py # In-memory issue tracker

yaml
Copy
Edit

---

## 🌐 API Endpoints

| Endpoint                       | Method | Description                          |
|-------------------------------|--------|--------------------------------------|
| `/health`                     | GET    | Health check                         |
| `/workflow/diagnose`          | POST   | Run diagnosis agent                  |
| `/suggest-patch`              | POST   | Run patch agent                      |
| `/workflow/triage`            | POST   | Triage raw issue data                |
| `/workflow/seed`              | POST   | Seed mock issue into memory          |
| `/run_autonomous_workflow`    | POST   | Run full AI → QA → PR workflow       |
| `/metrics/status`             | GET    | Agent + issue metrics (JSON)         |
| `/issues/inbox`               | GET    | List all new issues                  |
| `/issues/attention-needed`    | GET    | Show issues needing review           |

---

## 🛠️ Running Locally

```bash
# From the backend root
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
🌐 Deployment Notes
Component	Notes
API Gateway	Mounted via / or behind proxy (e.g. Vercel, Render)
Voice WS	Enable WebSocket support if running Gemini voice
CORS	Open in dev, restrict for production
GitHub Integration	Stubbed in create_fix_pull_request.py — integrate your token and org logic

📦 Environment Variables
Name	Purpose
OPENAI_API_KEY	For GPT-4o interactions
GEMINI_API_KEY	For Gemini agents & voice
GITHUB_TOKEN	For pull request automation

🧪 Seed Mock Issue Example
json
Copy
Edit
POST /workflow/seed

{
  "issue_id": "ISSUE-001",
  "title": "App crash on login",
  "description": "Login fails when username has emoji",
  "error_message": "UnicodeEncodeError",
  "logs": "...stack trace...",
  "relevant_files": ["auth.py"],
  "repository": "https://github.com/your-org/repo"
}
🧠 Powered By
OpenAI GPT-4o

Gemini Pro

FastAPI

Streamlit Dashboard

Discover Software Solutions
