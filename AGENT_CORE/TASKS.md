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

- [ ] **Phase 3: Modular Architecture (Phase 1 complete)**
  - [x] `src/environment.py` — `Location`, `Resource`, `Environment`, `THE_GROVE`
  - [x] `src/storage.py` — `StorageBackend` ABC + `SQLiteBackend`
  - [x] `src/skills.py` — `Skill` ABC, `SkillRegistry`, all 7 skills, `SKILL_REGISTRY`
  - [x] `src/db.py` — updated schema (`world_resources` table, env-seeding)
  - [x] `src/simulation.py` — refactored tick loop using new modules
  - [x] `main.py` — passes `THE_GROVE` to init/reset
  - [x] `src/llm.py` — fixed `_smart_fallback` inventory detection
  - [ ] Phase 2: Spatial partitioning + LLM batching + memory summarization
  - [ ] Phase 3: Selective WebSocket broadcast

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
