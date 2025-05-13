🧠 DebugIQ Backend

The backend for DebugIQ, an autonomous debugging and patching agent platform built using FastAPI, powered by GPT-4o, Gemini, and multi-agent orchestration.

Developed by Discover Software Solutions

This service performs automated diagnosis, patch suggestion, QA validation, pull request creation, and orchestrates multi-agent debugging workflows — enabling AI-assisted bug triage at scale.

🚀 Features

🤖 Autonomous Debugging Pipelines(run_autonomous_workflow.py)

Issue diagnosis → patch proposal → QA → PR

🎧 Bi-Directional Voice Debugging (WebSocket + Gemini)

Natural language input/output

Audio streaming and transcript-based analysis

💪 Patch Generation with LLM Agents

Git-style diff + human-readable explanation

✅ Validation & Auto-Documentation

QA loop validates patch before PR

🔗 GitHub PR Automation

Stubbed for open source, extensible to full CI/CD

📊 Agent & Workflow Metrics

JSON summaries via /metrics/status

🗃️ Mock In-Memory Issue Database

No external DB required for local testing

🔌 Pluggable Architecture

Add, swap, or scale agents modularly

🛡️ Architecture Overview

FastAPI
│
├── /app/api/
│   ├── autonomous_router.py         # Orchestrated workflows
│   ├── metrics_router.py            # Workflow/agent telemetry
│   ├── issues_router.py             # Issue tracking
│   ├── voice_ws_router.py           # Gemini voice via WebSocket
│   └── voice_interactive_router.py  # Text/audio voice agent
│
├── /scripts/
│   ├── run_autonomous_workflow.py     # 🧠 Main workflow runner
│   ├── platform_data_api.py           # Repo/code context handlers
│   ├── autonomous_diagnose_issue.py   # Root cause agent
│   ├── agent_suggest_patch.py         # Patch LLM agent
│   ├── validate_proposed_patch.py     # QA agent logic
│   ├── create_fix_pull_request.py     # PR creator (stubbed)
│   └── mock_db.py                     # Local issue memory

🌐 API Endpoints

Endpoint

Method

Description

/health

GET

Health check

/workflow/diagnose

POST

Run diagnosis agent

/suggest-patch

POST

Run patch agent

/workflow/triage

POST

Parse and categorize issue input

/workflow/seed

POST

Seed mock issue into memory

/run_autonomous_workflow

POST

Run full AI → QA → PR pipeline

/metrics/status

GET

Agent + workflow metrics

/issues/inbox

GET

List all incoming issues

/issues/attention-needed

GET

Issues requiring further triage

🛠️ Running Locally

# Clone and start DebugIQ backend
git clone https://github.com/discoversoftwaresolutions/debugiq-backend.git
cd debugiq-backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

🌐 Deployment Notes

Component

Notes

API Gateway

Mount / or proxy via Vercel, Render, or your platform

Voice WebSocket

Enable WS support for Gemini-based voice debugging

CORS

Allow all for dev; restrict for production

GitHub PR

Integrate your token/org logic into create_fix_pull_request.py

📦 Environment Variables

Variable

Purpose

OPENAI_API_KEY

GPT-4o model access

GEMINI_API_KEY

Gemini agents and audio processing

GITHUB_TOKEN

For GitHub PR automation (optional)

🧲 Example: Seed Mock Issue

POST /workflow/seed
Content-Type: application/json

{
  "issue_id": "ISSUE-001",
  "title": "App crash on login",
  "description": "Login fails when username has emoji",
  "error_message": "UnicodeEncodeError",
  "logs": "...stack trace...",
  "relevant_files": ["auth.py"],
  "repository": "https://github.com/your-org/repo"
}

🔒 License

Distributed under the Apache 2.0 License.See LICENSE for more information.

🤝 Contributing

We welcome contributions from the community! Please see our CONTRIBUTING.md for setup, issue guidelines, and PR processes.

🧠 Powered By

OpenAI GPT-4o

Gemini Pro

FastAPI

Streamlit

Discover Software Solutions

🌍 Join the Community

We are building a global community of developers who care about intelligent debugging, autonomous tooling, and AI-native software workflows.

Follow us:

X (formerly Twitter)

LinkedIn

Website

“Don’t just fix bugs — understand them, evolve from them, and automate their extinction.”— DebugIQ Team

