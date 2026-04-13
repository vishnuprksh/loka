"""
LLM integration via OpenRouter.
Falls back to heuristic survival logic when no API key is provided.
"""
import os
import json
import random
import requests

_raw_key = os.getenv("OPENROUTER_API_KEY", "")
# Ignore placeholder values that ship in .env.example
OPENROUTER_API_KEY = _raw_key if (len(_raw_key) > 20 and "your_" not in _raw_key) else ""
MODEL = os.getenv("LOKA_MODEL", "google/gemma-3-4b-it:free")
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm(prompt: str) -> dict:
    """Call the LLM and return a parsed action dict."""
    if not OPENROUTER_API_KEY:
        return _smart_fallback(prompt)

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
        print(f"[LLM] Error: {exc} — using fallback.")
        return _smart_fallback(prompt)


def _parse_action(content: str) -> dict:
    """Extract a JSON action object from LLM output."""
    try:
        return json.loads(content)
    except Exception:
        pass
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass
    return {"thought": "I'm confused.", "action": "DO_NOTHING", "target": None, "message": None}


def _smart_fallback(prompt: str) -> dict:
    """Heuristic agent behaviour when no LLM is available."""
    import re

    hunger, energy, location = 5, 5, "fire_pit"
    has_berry = "berry" in prompt and "empty" not in prompt

    try:
        # Use \s+ to tolerate alignment spaces in the prompt template
        m = re.search(r"Hunger:\s+(\d+)/10", prompt)
        if m:
            hunger = int(m.group(1))
        m = re.search(r"Energy:\s+(\d+)/10", prompt)
        if m:
            energy = int(m.group(1))
        m = re.search(r"Location:\s+(\w+)", prompt)
        if m:
            location = m.group(1)
    except Exception:
        pass

    # Critical survival first (threshold raised to 6 for ample margin)
    if hunger <= 6 and has_berry:
        return {"thought": "I must eat NOW.", "action": "EAT", "target": None, "message": None}
    if hunger <= 6 and location == "berry_bush":
        return {"thought": "Foraging desperately.", "action": "FORAGE", "target": None, "message": None}
    if hunger <= 6:
        return {"thought": "Heading to the berry bush.", "action": "MOVE_TO", "target": "berry_bush", "message": None}

    # Energy management
    if energy <= 3:
        if location == "shelter":
            return {"thought": "Resting deeply.", "action": "SLEEP", "target": None, "message": None}
        return {"thought": "Exhausted. Need shelter.", "action": "MOVE_TO", "target": "shelter", "message": None}
    if location == "shelter" and energy < 8:
        return {"thought": "Still recovering.", "action": "SLEEP", "target": None, "message": None}

    # Opportunistic foraging
    if location == "berry_bush" and hunger < 9:
        return {"thought": "Collecting food while I can.", "action": "FORAGE", "target": None, "message": None}

    # Social / idle
    options = [
        ("MOVE_TO", "fire_pit", "I want company."),
        ("MOVE_TO", "berry_bush", "I'll find food."),
        ("DO_NOTHING", None, "I observe the grove quietly."),
    ]
    thought, action, target = random.choice(
        [(t, a, tg) for a, tg, t in options]
    )
    return {"thought": thought, "action": action, "target": target, "message": None}
