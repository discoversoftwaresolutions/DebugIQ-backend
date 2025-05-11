# File: scripts/utils/ai_api_client.py

import os
import openai
import google.generativeai as genai
import logging

# Configure logger
logger = logging.getLogger("debugiq.ai_client")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] - %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

# --- OpenAI Setup ---
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"

# --- Gemini Setup ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "models/gemini-pro"

def call_codex(prompt: str) -> str:
    try:
        logger.info("Calling OpenAI Codex (GPT-4o)...")
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior debugging assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI Codex call failed: {e}")
        return f"[Codex Error] {str(e)}"

def call_gemini(prompt: str) -> str:
    try:
        logger.info("Calling Google Gemini for voice command...")
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini call failed: {e}")
        return f"[Gemini Error] {str(e)}"

def call_ai_agent(task_type: str, prompt: str) -> str:
    if task_type == "voice_command":
        return call_gemini(prompt)
    return call_codex(prompt)
