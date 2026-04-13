# Strategic Memories
### 2026-04-13 - Global Death Notifications
- **Context:** Previously, when an agent died, it was only recorded in the system chronicle. Other agents remained unaware unless they were at the same location (and even then, only via vague history).
- **Decision:** Modified [src/simulation.py](src/simulation.py) to broadcast a "perished" memory to all surviving agents whenever an agent dies.
- **Reasoning:** Global awareness of death creates a sense of mortality and urgency in the survivors. It allows them to reflect on the loss of their peers and adjusts their survival priorities without needing to find the body.

### 2026-04-13 - Increased Stat Decay Frequency
- **Context:** User requested that hunger and energy decrease by 1 on every single tick.
- **Decision:** Modified [src/storage.py](src/storage.py) to remove the modulo-based slower decay and instead apply a -1 update to all living agents every tick.
- **Reasoning:** Increasing the decay rate makes survival significantly more challenging, forcing agents to prioritize foraging and resting more frequently, and likely increasing the frequency of social resource requests earlier in their life cycles.

### 2026-04-13 - State Bar Renaming for Prompt Clarity
- **Context:** Agents (e.g., Dax) were confused by "Hunger: 9/10," thinking it meant they were 90% hungry rather than 90% full.
- **Decision:** Renamed prompt labels to "Energy/Fullness" and "Rest/Vigor" with explicit 0=STARVING/EXHAUSTED and 10=FULL/RESTED indicators.
- **Reasoning:** Improving prompt clarity prevents agents from wasting actions on foraging/sleeping when they are already at near-max capacity, leading to more efficient survival and more time for social/path-related goals.

### 2026-04-13 - Removed Cross-Decay & Increased Thresholds
- **Context:** Dax and Kael died due to a "death spiral" where low hunger/energy drained each other too quickly for agents to react or ask for help.
- **Decision:** Removed the cross-decay logic from `src/storage.py` and increased `HUNGER_THRESHOLD_LOW` / `ENERGY_THRESHOLD_LOW` from 3 to 5 in `src/config.py`.
- **Reasoning:** Giving agents a larger safety buffer (5 instead of 3) and removing the double-drain penalty makes the simulation more forgiving and allows more time for social intervention (asking for food) before death.

### 2026-04-13 - Survival Interdependency (Obsolete)
- **Context:** Decoupled stats allow for easier survival without consequences until zero.
- **Decision:** Implemented cross-decay where Hunger <= 3 causes Energy loss, and Energy <= 3 causes Hunger loss.
- **Reasoning:** Superseded by "Removed Cross-Decay" decision due to unintended agent death spirals.

### 2026-04-13 - Modularized Simulation Constants
- **Context:** User requested lowering max stats from 20 to 10 and requested a modular way to manage these values.
- **Decision:** Created `src/config.py` to hold simulation-wide constants (MAX_STAT_VALUE, thresholds, resource defaults).
- **Reasoning:** Hardcoding magic numbers across multiple files makes balancing difficult. Centralizing these in a config module allows for rapid iteration and ensures consistency between the backend state, LLM prompts, and frontend visualization.

### 2026-04-13 - Increased Scarcity to Drive Competition
- **Context:** Previous reduction to 10 berries was still slightly too abundant for high-tension social dynamics.
- **Decision:** Reduced berry `max_count` further (10 -> 6).
- **Reasoning:** Extremely limited resources force agents to either coordinate strictly or compete aggressively, highlighting their sociability and greed traits more effectively.

### 2026-04-13 - Reduced Resource Abundance to Drive Social Interaction
- **Context:** Observed that survival being "too easy" led to reduced social interaction as agents became self-sufficient.
- **Decision:** Reduced berry `max_count` (20 -> 10) and `harvest_yield` (2 -> 1). Updated frontend to show inventory counts (e.g., "berry x5") to better visualize scale.
- **Reasoning:** Scarcity is a primary driver of societal development, trade, and social negotiation.

### 2026-04-13 - Relaxed Agent Survival Stats
- **Context:** Agents were overly focused on survival (hunger/energy) due to rapid stat depletion, stifling social interaction.
- **Decision:** Doubled max stats (10 -> 20), halved decay frequency (tick-based logic), and updated prompt thresholds.
- **Reasoning:** Increasing the "buffer" give agents more mental space to pursue social and path-related goals (Merchant/Scholar/Leader) without immediate fear of death.

### 2026-04-13 - Clear DB on Startup
- **Context:** Fresh simulation runs are preferred for testing and observation.
- **Decision:** Replaced `init_db` with `reset_db` in `main.py` lifespan.
- **Reasoning:** Ensures every server start begins at Tick 0 with fresh agents, preventing accumulated state from polluting new observation sessions.

### [2026-04-13] - Removed Fallback Logic
- **Context:** User felt fallback heuristics "spoiled the fun" of AI autonomy.
- **Decision:** Entirely removed `_smart_fallback` from `src/llm.py`.
- **Reasoning:** In line with the "Zero-Touch Autonomy" principle, agents should only act based on LLM decisions. If the API fails or is missing, agents now `DO_NOTHING` to avoid breaking the simulation with hardcoded "magic" behavior.
- **Result:** Pure LLM-driven simulation. If `OPENROUTER_API_KEY` is missing, agents freeze with a "No API key" thought.

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

### 2026-04-13 - Multi-party Location-based Communication
- **Context:** User requested that communication no longer be one-to-one; anyone in the same location should hear the speech.
- **Decision:** Refactored `TalkSkill` to broadcast to all agents at the current location. Added a 'location' column to the `memories` table to track where conversations occur. Updated the prompt builder to include a "Nearby" context section showing overheard conversations at the agent's current location. Added support for 'everyone' as a target for broad announcements.
- **Reasoning:** Simulates realistic spatial audio/social presence. Forcing agents to be "aware" of other conversations in the same location encourages collective emergent behavior rather than isolated bilateral trades.
