# Loka MVP: Detailed Technical Architecture

The goal of this MVP is to prove **social autonomy** within "The Grove." It will be a Python-based backend with a simple real-time CLI (command-line) "observer" view.

## 1. Data Models (The State)

### A. World State (`world.json`)
```json
{
  "tick": 142,
  "locations": {
    "fire_pit": {"x": 10, "y": 10, "entities": ["agent_1", "agent_2"]},
    "berry_bush": {"x": 2, "y": 18, "resources": 15},
    "shelter": {"x": 18, "y": 2, "slots": 5}
  }
}
```

### B. Agent DNA (`agent_dna.json`)
```json
{
  "id": "agent_1",
  "name": "Kael",
  "traits": {"greed": 0.2, "sociability": 0.9, "curiosity": 0.5},
  "stats": {"hunger": 4, "energy": 7, "community": 8},
  "location": [10, 10]
}
```

---

## 2. The Simulation Loop (The Engine)

The simulation runs in "Ticks" (e.g., 1 tick = 1 minute of world time).

1.  **Perception:** For each agent, gather "What I see" (e.g., "Agent B is near," "The fire is out," "There are berries nearby").
2.  **Memory Recall:** Retrieve the last 3-5 relevant memories (e.g., "Last time I saw Agent B, they didn't share food").
3.  **LLM Prompting:**
    - **Input:** DNA + Stats + Perception + Memories.
    - **Prompt:** "You are Kael. You are hungry. Agent B is nearby. You have 15 berries. What is your INTENT and ACTION?"
    - **Output (JSON):** `{"thought": "I should share a berry to gain favor.", "action": "GIVE_ITEM", "target": "Agent B", "item": "berry"}`
4.  **Transformation:** The engine validates the action and updates `world.json` and `agent_dna.json`.
5.  **Logging:** Save the result to `chronicle.log`.

---

## 3. Technology Stack (The Minimalist Choice)

- **Language:** Python 3.11+
- **Backend Framework:** FastAPI (For future web exposure, but run locally for now).
- **AI Integration:** OpenAI API or LangChain (to interface with GPT-4o-mini).
- **Persistent Storage:** 
  - **Relational:** SQLite (Simple, single file).
  - **Vector (Memory):** ChromaDB (Local, installs via pip).
- **UI:** A simple CLI script that prints the 20x20 grid using emojis in the terminal.

---

## 4. MVP "Character Creation" Flow

1.  User runs `python create_agent.py`.
2.  Input: Name, choosing 3 "Gene" sliders (e.g., Friendly vs. Grumpy).
3.  The agent is injected into `world.json`.
4.  User runs `python loka_sim.py` and watches the logs.

---

## 5. Success Criteria for MVP
- An agent decides to eat when hungry without being told.
- Two agents meet at the fire and have a coherent (logged) conversation.
- One agent's behavior changes based on a "memory" of another agent.
