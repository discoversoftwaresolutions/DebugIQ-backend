# File: utils/call_ai_agent.py

import requests
import os

# These should be securely managed in production
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-key")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-key")

GPT_MODEL = "gpt-4o"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + GEMINI_API_KEY


def call_ai_agent(task_type: str, payload: dict) -> dict:
    """
    Routes task to GPT-4o or Gemini based on task_type.
    Returns the raw agent result or raises error.
    """
    if task_type in {"suggest_patch", "qa", "generate_doc"}:
        return _call_gpt4o(task_type, payload)
    elif task_type in {"voice_command", "transcribe", "intent"}:
        return _call_gemini(task_type, payload)
    else:
        return {"error": f"Unknown task type: {task_type}"}


def _call_gpt4o(task_type: str, payload: dict) -> dict:
    """Calls OpenAI's GPT-4o model for text tasks."""
    prompt_map = {
        "suggest_patch": "Given this code, diagnose the error and suggest a patch.",
        "qa": "Validate this code for logic and syntax correctness.",
        "generate_doc": "Document the following patch as a clear summary for developers."
    }

    prompt = prompt_map.get(task_type, "Perform task.")
    code = payload.get("code", "")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": GPT_MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": code}
        ],
        "temperature": 0.2
    }

    try:
        res = requests.post(OPENAI_URL, headers=headers, json=body, timeout=20)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        return {"result": content}
    except Exception as e:
        return {"error": str(e)}


def _call_gemini(task_type: str, payload: dict) -> dict:
    """Calls Gemini for voice-related or conversational tasks."""
    try:
        body = {
            "contents": [
                {"role": "user", "parts": [{"text": payload.get("text", "")}]}
            ]
        }

        res = requests.post(GEMINI_URL, headers={"Content-Type": "application/json"}, json=body, timeout=15)
        res.raise_for_status()
        candidates = res.json().get("candidates", [])
        if candidates:
            return {"result": candidates[0]["content"]["parts"][0]["text"]}
        return {"error": "No Gemini response."}
    except Exception as e:
        return {"error": str(e)}
