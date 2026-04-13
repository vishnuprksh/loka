"""
LLM integration via OpenRouter.
Requires OPENROUTER_API_KEY to be set in .env.
"""
import os
import json
import requests

_raw_key = os.getenv("OPENROUTER_API_KEY", "")
# Ignore placeholder values that ship in .env.example
OPENROUTER_API_KEY = _raw_key if (len(_raw_key) > 20 and "your_" not in _raw_key) else ""
MODEL = os.getenv("LOKA_MODEL", "qwen/qwen3.6-plus")
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm(prompt: str) -> dict:
    """Call the LLM and return a parsed action dict."""
    if not OPENROUTER_API_KEY:
        print("[LLM] No API key found. Simulation halted (no-fallback mode).")
        return {"thought": "I am frozen in time (no API key).", "action": "DO_NOTHING", "target": None, "message": None}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/vishnuprksh/loka",
        "X-Title": "Loka - The Grove",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85,
        "max_tokens": 200,
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return _parse_action(content)
    except Exception as exc:
        print(f"[LLM] Error: {exc} — returning DO_NOTHING.")
        return {"thought": f"The void is calling... (Error: {exc})", "action": "DO_NOTHING", "target": None, "message": None}


def _parse_action(content: str) -> dict:
    """Extract a JSON action object from LLM output."""
    default_resp = {"thought": "I'm confused.", "action": "DO_NOTHING", "target": None, "message": None, "conversation_status": "END"}
    try:
        data = json.loads(content)
        if "conversation_status" not in data:
            data["conversation_status"] = "END"
        return data
    except Exception:
        pass
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
            if "conversation_status" not in data:
                data["conversation_status"] = "END"
            return data
    except Exception:
        pass
    return default_resp
