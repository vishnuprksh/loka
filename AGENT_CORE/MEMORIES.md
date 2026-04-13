### [2026-04-13] - Phase 1 Modular Architecture Implemented
- **Context:** User wanted modularity so adding resources/skills doesn't require core changes
- **Decision:** Three new modules: `environment.py` (config), `storage.py` (DB abstraction), `skills.py` (pluggable actions)
- **Reasoning:** Single responsibility — `simulation.py` tick loop never changes when resources or skills are added; `THE_GROVE` in `environment.py` is the single place to extend the world; `SKILL_REGISTRY` in `skills.py` is the single place to add actions
- **DB change:** Replaced hardcoded `world.berry_count` with generic `world_resources` table (name, count, max_count); existing `loka.db` auto-migrates on `reset_db(THE_GROVE)` call
- **Compat:** Frontend `berry_count` key preserved in `get_state_dict()`; new `resources` dict also available

### 2026-04-13 - Project Inception
- **Context:** User wants to build a virtual world ("Loka") where AI agents and humans interact to form a society.
- **Decision:** Use a structured `AGENT_CORE` system to manage the project's evolution.
- **Reasoning:** A complex simulation requires clear architectural boundaries and a "North Star" to avoid scope creep.

### 2026-04-13 - Shift to Full Autonomy
- **Context:** User requested a completely autonomous system with zero interaction after character creation.
- **Decision:** Remove the "Player Avatar" and "Visitor" roles. The user now enters as an "Observer" or "Chronicler."
- **Reasoning:** Shifting the focus from a "game" to a "simulated society" requires more robust internal agent motivations and less reliance on player-driven events.

### 2026-04-13 - MVP Tech Stack Lock-in
- **Context:** Deciding how to build the most efficient prototype.
- **Decision:** Python + SQLite + ChromaDB + CLI Visualization.
- **Reasoning:** Minimizes overhead on frontend development to focus entirely on the LLM-driven autonomy and memory systems.

### 2026-04-13 - Parallelization Support
- **Context:** User raised concern about LLM latency exceeding tick interval.
- **Decision:** Transitioned the simulation loop to use `concurrent.futures.ThreadPoolExecutor` for agent "thinking" cycles.
- **Reasoning:** Sequential LLM calls stack latency. Parallelization ensures Total Latency is the max latency, keeping the tick rate stable as agent count increases.

### 2026-04-13 - Conversational Continuity & Database Schema Update
- **Context:** Chats were "one sided" and repetitive because agents lacked context about what was being said to them.
- **Decision:** Updated `memories` table to store `target` and `message` columns. Modified prompt builder to include a larger window (20) of memories with specific social highlighting. Updated heuristic fallback to "read" the last message from the prompt and respond contextually.
- **Reasoning:** Without persistent message storage, the LLM/Heuristic only sees the simulation's "event log" but not the actual dialogue content, preventing genuine interaction. Longer memory windows and semantic parsing are needed for conversational coherence.
