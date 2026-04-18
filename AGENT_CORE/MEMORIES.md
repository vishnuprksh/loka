# Strategic Memories

### 2026-04-18 - World-Independent Agent Self-Reflection Architecture
- **Context:** Agents had no mechanism to learn from past decisions or recognize behavioral patterns. Previous attempts to add reflection were world-dependent (e.g., "Did you achieve 30 gold?"), breaking portability.
- **Decision:** Implemented minimal forced self-reflection via recent thought history. Added `thought_history` JSON column to agents table (stores last 3 thoughts). Prompt now includes "YOUR RECENT DECISIONS" section with world-agnostic reflection questions: "Are you repeating? Is this working? What would you try differently?"
- **Reasoning:** This architecture is world-independent—agents can be dropped into any environment without hardcoded goal references. Self-reflection is purely agent-relative ("Did YOUR approach work?"), not system-measured. Thought history tracks memory automatically via existing `last_thought` persistence, requiring no new game logic.
- **Files Changed:** `src/db.py` (added column), `src/config.py` (SELF_REFLECTION_PROMPT), `src/simulation.py` (extract/display thoughts), `src/storage.py` (maintain history).

### 2026-04-16 - UI Visibility Adjustment (Agent Thought)
- **Context:** Agent thoughts were being truncated or not fully visible due to small font and CSS constraints.
- **Decision:** Increased `.agent-thought` font size to `0.8rem` and removed `min-height` in [static/index.html](static/index.html).
- **Reasoning:** Agent inner monologue is critical for the "Observer" experience. Removing height constraints allows the container to expand naturally.

### 2026-04-16 - Win Condition and Gold Objectives
- **Context:** The user clarified that there are 4 agents, each starting with 10 gold, and the goal is to reach 30 gold.
- **Decision:** Updated `WIN_CONDITION_GOLD` to 30 and added `STARTING_GOLD` = 10 to [src/config.py](src/config.py). Updated `GAME_RULES` prompt to explicitly mention the starting amount. Ensured starter agents are seeded with this amount in [src/simulation.py](src/simulation.py).
- **Reasoning:** Providing agents with their starting context and a clear "finish line" encourages more strategic behavior regarding gold accumulation and social exchanges.

### 2026-04-16 - mandatory Sleep and Resting Buff
- **Context:** Energy was previously a non-lethal stat used mostly for action gating.
- **Decision:** Updated [src/storage.py](src/storage.py) and [src/simulation.py](src/simulation.py) to make Energy-at-Zero (0) fatal.
- **Reasoning:** Elevation of Energy to a critical survival stat (like Hunger) forces better long-term planning and makes resting locations (Shelter/Fire Pit) strategically vital. Hunger also pauses while resting to provide more survival breathing room.

### 2026-04-16 - Randomized Action Application
- **Context:** Resource harvesting (Foraging) was biased towards agents with lower IDs because they were processed sequentially.
- **Decision:** Shuffled the results of parallel LLM thinking before applying them to the world state in [src/simulation.py](src/simulation.py).
- **Reasoning:** Ensures fairness in resource competition. In a survival simulation, deterministic "speed" based on database order breaks immersion and creates unfair advantages.

### 2026-04-16 - Observer Frequency and Evaluation Logic
- **Context:** User requested less frequent but more analytical observer reports.
- **Decision:** Changed observer frequency to once every 5 ticks and added "Success" (Emergence) vs "Failure" (Roboticism) metrics.
- **Reasoning:** A 5-tick window provides enough context for the LLM to identify patterns (robotic) or surprises (emergent) that a single-tick view misses, while reducing LLM overhead.

### 2026-04-16 - Commercial Vision: Office Simulation
- **Context:** Documented the long-term commercial potential of the Loka engine.
- **Decision:** Identified "Office Simulation" as a primary use-case for predicting social dynamics and project roles based on "agent DNA" (personality).
- **Reasoning:** The emergence of negotiation and work-life balance in the current berry-foraging simulation validates that character traits drive complex group outcomes, making it applicable to corporate environments.

### 2026-04-14 - Fixed Chronicle and Observer Logging
- **Context:** The "Chronicles" tab was empty in the frontend, and the Observer LLM was failing to parse logs.
- **Decision:** Implemented `renderChronicle` in [static/index.html](static/index.html) and fixed a dictionary access bug in [src/observer.py](src/observer.py) (`r[entry]` -> `r['entry']`).
- **Reasoning:** Functional visibility is critical for the "Observer" role. Correcting the data flow ensures users can track the history of the world in real-time.

### 2026-04-14 - Fixed Resource Over-Harvesting Bug
- **Context:** Multiple agents were able to forage the same resource in a single tick because the resource state was snapshotted once at the start of the execution phase.
- **Decision:** Updated [src/simulation.py](src/simulation.py) to refresh `resource_state` from the database before each agent's turn and after each individual action.
- **Reasoning:** Sequential execution of agent actions must respect the real-time consumption of resources to maintain scarcity. This ensures that if only 1 berry exists, only the first agent to act can harvest it.

### 2026-04-14 - Primitive Social-Economic Logic
- **Context:** Agents were treating resource trades like a modern retail transaction, which mismatch the "tribe" survivor setting.
- **Decision:** Updated Behavioral Guidelines to prioritize sharing with friends and exploitation of others.
- **Reasoning:** In a primitive setting, resource sharing is a survival strategy for the group (friends), while external trading is a way to build a personal safety net (Gold). This creates a more dynamic social gap between allies and strangers.

### 2026-04-14 - Move to Multi-Action Architecture
- **Context:** Agents were limited to one atomic task per tick, which felt unnatural (e.g., can't talk while eating).
- **Decision:** Transitioning to an `actions` list schema in the cognitive loop.
- **Reasoning:** Multi-actions allow for richer social emergence and more realistic survival behavior without increasing the number of LLM calls (and thus cost).

### 2026-04-14 - Personality Trait Context in Prompts
- **Context:** Raw trait values like "Greed: 0.7" lacked standard scale or behavioral context for the LLM.
- **Decision:** Updated [src/simulation.py](src/simulation.py) to include a "PERSONALITY (Scale 0.0 to 1.0)" section with descriptive anchors for each trait (Greed, Sociability, Curiosity, Empathy, Assertiveness).
- **Reasoning:** Defining the scale (0.0 to 1.0) and providing qualitative descriptions (e.g., "prioritize wealth over social harmony") ensures the LLM interprets stats as behavioral biases rather than arbitrary numbers, leading to more consistent role-playing and alignment with the agent's defined path.

### 2026-04-14 - Social Survival via Emergency Calls
- **Context:** Agents were dying silently without leveraging the community for help when stats were critical.
- **Decision:** Integrated emergency prompts when stats hit a `DANGER_THRESHOLD` (2), instructing agents to use `TALK` to request assistance. Expanded the general "World Info" section with survival tips.
- **Reasoning:** Leverages the existing `TALK` skill and multi-action system to simulate realistic social distress calls. Explicitly telling agents to ask for help reduces the "hallucination" that they must survive solo.

### 2026-04-14 - Implementing Informed Agency
- **Context:** Agents were dying or making poor decisions due to lack of knowledge about world mechanics (stats, resources, trading).
- **Decision:** Added a dedicated "Info Section" to agent prompts and a persistent `info` field in the database for personalized agent knowledge. 
- **Reasoning:** Providing explicit mechanics (e.g., "berry gives 5 points") reduces "hallucinated" strategies and allows agents to plan survival and social moves more effectively. Social bar visibility is key for emergent popularity dynamics.

### 2026-04-14 - Berry Hunger Restoration Increased
- **Context:** Eating a berry should restore a meaningful amount of hunger rather than a minimal amount.
- **Decision:** Set `DEFAULT_BERRY_HUNGER` to 5 in [src/config.py](src/config.py).
- **Reasoning:** A stronger food reward makes berry consumption materially useful during survival pressure while preserving the existing scarcity tuning.

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
