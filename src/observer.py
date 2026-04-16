"""
The Observer — Iterative world reporter.
Analyses chronicle logs on every tick to provide a concise, clear report.
Uses the last report as context to maintain continuity and reduce prompt size.
"""
import json
from .llm import call_llm
from .storage import StorageBackend

OBSERVER_PROMPT = """
You are The Observer of Loka, an autonomous virtual world. 
Your goal is to provide a situational report and project evaluation for the last 5 ticks.

CONTEXT:
- Previous Report: {last_report}
- New Chronicle Logs (Ticks {start_tick} to {end_tick}):
{logs}

INSTRUCTIONS:
1. SITUATIONAL REPORT: Synthesize the logs into a clear, punchy update (2-3 sentences).
2. PROJECT SUCCESS: Identify something NEW or SURPRISING that happened without specific instructions (emergent behavior, e.g., agents developing a trade ritual, helping a stranger without prompts). 
3. PROJECT FAILURE: Identify REPEATED or ROBOTIC patterns that feel unnatural or "looping" (e.g., agents repeating the same greeting for 5 ticks, walking in circles, or failing to react to a crisis).
4. Output format:
   REPORT: [Text]
   SUCCESS: [Text]
   FAILURE: [Text]
"""

def update_observer_report(tick: int, storage: StorageBackend) -> str:
    """Fetch logs from the last 5 ticks and generate an evaluation report."""
    # 1. Get last report
    conn = storage.get_conn()
    last_row = conn.execute("SELECT report FROM observer_report ORDER BY tick DESC LIMIT 1").fetchone()
    last_report = last_row["report"] if last_row else "No previous reports. The world has just begun."

    # 2. Get logs for the last 5 ticks
    start_tick = max(0, tick - 4)
    logs_rows = conn.execute(
        "SELECT entry FROM chronicle WHERE tick BETWEEN ? AND ? ORDER BY tick ASC",
        (start_tick, tick)
    ).fetchall()
    conn.close()

    logs_text = "\n".join([f"- {r['entry']}" for r in logs_rows]) or "Nothing notable happened."

    # 3. Call LLM
    prompt = OBSERVER_PROMPT.format(
        last_report=last_report,
        start_tick=start_tick,
        end_tick=tick,
        logs=logs_text
    )
    
    new_report = _call_observer_llm(prompt)

    # 4. Persistence
    if "The Observer is silent" not in new_report:
        conn = storage.get_conn()
        with conn:
            conn.execute("""
                INSERT INTO observer_report (tick, report) 
                VALUES (?, ?)
            """, (tick, new_report))
        conn.close()

    return new_report

def _call_observer_llm(prompt: str) -> str:
    """Internal helper for raw text response from LLM using existing LLM config."""
    from .llm import OPENROUTER_API_KEY, MODEL, API_URL
    import requests

    if not OPENROUTER_API_KEY:
        return "The Observer is silent (No API key)."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/vishnuprksh/loka",
        "X-Title": "Loka - The Observer",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 150,
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return f"Observer Error: {exc}"
