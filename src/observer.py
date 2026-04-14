"""
The Observer — Iterative world reporter.
Analyses chronicle logs on every tick to provide a concise, clear report.
Uses the last report as context to maintain continuity and reduce prompt size.
"""
import json
from .llm import call_llm
from .storage import StorageBackend

OBSERVER_PROMPT = \"\"\"
You are The Observer of Loka, an autonomous virtual world. 
Your goal is to provide a concise, high-level situational report for the current tick.

CONTEXT:
- Previous Report: {last_report}
- New Chronicle Logs (Tick {tick}):
{logs}

INSTRUCTIONS:
1. Synthesize the new logs into a clear, punchy update (2-4 sentences).
2. Use the "Previous Report" to avoid repeat data and track evolving trends (e.g., "Dax is still starving" vs just "Dax is hungry").
3. Focus on: Social shifts, resource scarcity, deaths, or unusual agent behavior.
4. Output ONLY the report text. No headers, no JSON.
\"\"\"

def update_observer_report(tick: int, storage: StorageBackend) -> str:
    \"\"\"Fetch latest logs, get last report, and generate a new one via LLM.\"\"\"
    # 1. Get last report
    conn = storage.get_conn()
    last_row = conn.execute("SELECT report FROM observer_report ORDER BY tick DESC LIMIT 1").fetchone()
    last_report = last_row["report"] if last_row else "No previous reports. The world has just begun."

    # 2. Get logs for this tick
    # Note: We assume add_chronicle was called before this
    logs_rows = conn.execute("SELECT entry FROM chronicle WHERE tick = ? (SELECT tick FROM world WHERE id=1)", (tick,)).fetchall()
    # Actually, we want logs for the current tick specifically
    logs_rows = conn.execute("SELECT entry FROM chronicle WHERE tick = ?", (tick,)).fetchall()
    conn.close()

    logs_text = \"\\n\".join([f"- {r['entry']}" for r in logs_rows]) or "Nothing notable happened."

    # 3. Call LLM
    prompt = OBSERVER_PROMPT.format(
        last_report=last_report,
        tick=tick,
        logs=logs_text
    )
    
    # We use call_llm but we need a plain text response. 
    # Since call_llm currently expects JSON, we might need a variant or just parse it.
    # However, to avoid modifying src/llm.py too much, let's see if we can use it.
    # Actually, let's add a raw_call_llm or similar if needed.
    # For now, I'll rely on call_llm returning a dict and I'll use the 'thought' or parse.
    # Better: I'll use the same calls as in llm.py but for raw text.
    
    new_report = _call_observer_llm(prompt)

    # 4. Persistence
    conn = storage.get_conn()
    with conn:
        conn.execute(\"\"\"
            INSERT INTO observer_report (tick, report) 
            VALUES (?, ?)
        \"\"\", (tick, new_report))
    conn.close()

    return new_report

def _call_observer_llm(prompt: str) -> str:
    \"\"\"Internal helper for raw text response from LLM using existing LLM config.\"\"\"
    from .llm import OPENROUTER_API_KEY, MODEL, API_URL
    import requests

    if not OPENROUTER_API_KEY:
        return \"The Observer is silent (No API key).\"

    headers = {
        \"Authorization\": f\"Bearer {OPENROUTER_API_KEY}\",
        \"Content-Type\": \"application/json\",
        \"HTTP-Referer\": \"https://github.com/vishnuprksh/loka\",
        \"X-Title\": \"Loka - The Observer\",
    }
    payload = {
        \"model\": MODEL,
        \"messages\": [{\"role\": \"user\", \"content\": prompt}],
        \"temperature\": 0.7,
        \"max_tokens\": 150,
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()[\"choices\"][0][\"message\"][\"content\"].strip()
    except Exception as exc:
        return f\"Observer Error: {exc}\"
