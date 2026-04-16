# Project Overview: Loka
**North Star:** Create a fully autonomous virtual world where AI agents live, interact, and evolve their own society without human intervention, where users are observers of an emerging civilization.

**Core Architecture:**
- **Frontend:** Real-time 2D/3D visualization for observation (The "Observer Portal").
- **Backend:** High-throughput autonomous simulation engine (World State + Agent Tick).
- **AI Engine:** Self-driving cognitive loop for agents (Observation -> Reflection -> Intent -> Action).
- **Database:** Persistence for agent life histories and societal evolution.

**Guiding Principles:**
- **Zero-Touch Autonomy:** Agents make all decisions; users only observe.
- **Emergent Society:** Rules, hierarchies, and culture should emerge from agent interactions.
- **Persistence:** The simulation runs continuously, even when no user is watching.
- **Informed Agency:** Agents should have access to world rules and mechanics (including lethality of exhaustion) to make better survival and social decisions.

**Constraints:**
- Scalability of LLM calls (Cost and Latency).
- Consistency of world state across multiple concurrent interactions.
- **Dual Survival Condition:** Agents perish if either hunger OR energy deplete to zero.
- **Resting Stat Preservation:** Resting at key locations (shelter/fire_pit) stops hunger decay and promotes energy recovery.
