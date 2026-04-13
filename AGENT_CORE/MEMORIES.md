# Strategic Memories

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

### 2026-04-13 - Latency Handling (Parallelization)
- **Context:** User raised concern about LLM latency exceeding tick interval.
- **Decision:** Transitioned the simulation loop to use `concurrent.futures.ThreadPoolExecutor` for agent "thinking" cycles.
- **Reasoning:** Sequential LLM calls stack latency ($\text{Total Latency} = \sum \text{latency}_i$). Parallelization ensures $\text{Total Latency} = \max(\text{latency}_i)$, keeping the tick rate stable as agent count increases.
