## 🧠 Task Tree

- [ ] **Phase 1: Foundation & Planning**
  - [x] Initial Architecture Brainstorming
  - [x] Simple World Setting ("The Grove") defined
  - [x] MVP Architecture Detailed
  - [x] AI Studio Prompt Created (Language-Independent)

- [ ] **Phase 2: MVP Implementation (Python/FastAPI)**
  - [x] Agent SQLite State Manager (src/db.py)
  - [x] Autonomous Decision Loop + Heuristic Fallback (src/llm.py)
  - [x] Simulation Engine with Tick Loop (src/simulation.py)
  - [x] FastAPI Server + WebSocket Real-time Broadcast (main.py)
  - [x] Observer Portal Frontend (static/index.html)
  - [x] Server running — agents surviving autonomously at tick 37+
  - [x] Parallelized LLM calls to handle Latency vs. Tick drift

- [ ] **Phase 3: LLM Integration (Real Social Behaviour)**
  - [ ] Set real OPENROUTER_API_KEY in .env
  - [ ] Verify agent TALK and GIVE_BERRY actions fire via LLM
  - [ ] Tune prompts for emergent cultural norms
  - [ ] World State Management (Grid/Region system)
  - [ ] Time & Event Loop

- [ ] **Phase 3: Social & Interaction Layer**
  - [ ] Communication Protocol (Speech/Gesture)
  - [ ] Relationship Mapping
  - [ ] Resource/Economic System

- [ ] **Phase 4: User Integration**
  - [ ] Avatar Creation & Control
  - [ ] Observer Mode
  - [ ] Web/Desktop Interface

---

## 🚧 Blockers
- None currently. Initializing project structure.
