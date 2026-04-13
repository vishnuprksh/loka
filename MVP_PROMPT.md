# LOKA MVP - AI Studio Prompt (Language Independent)

Copy this entire prompt into your AI Studio of choice (Claude, ChatGPT, etc.) to begin building the MVP.

---

## PROJECT CONTEXT

**Project Name:** Loka  
**Vision:** A fully autonomous virtual world where AI agents live, interact, and evolve their own society without human intervention. Users observe and create new agents, but cannot control them.

**MVP Scope:** Prove autonomous agent behavior in a single location called "The Grove." Two agents should demonstrate survival instincts, social memory, and emergent decision-making.

---

## THE WORLD: "The Grove"

A simple 20x20 grid with three key locations:
- **Fire Pit (10, 10):** Social hub where agents gather and communicate.
- **Berry Bushes (2, 18):** Food source; agents forage here. Max 20 berries available.
- **Shelter (18, 2):** Where agents rest and recover energy.

Each location can hold multiple agents. When an agent's hunger reaches 0, they leave the world.

---

## AGENT DATA MODEL

### Agent DNA (Created Once, Immutable)
```
{
  "id": "unique_identifier",
  "name": "AgentName",
  "traits": {
    "greed": 0.0-1.0,           // How much they hoard vs share
    "sociability": 0.0-1.0,     // Preference for being near others
    "curiosity": 0.0-1.0        // Interest in exploring vs routine
  },
  "memory_log": [               // Growing list of past events
    {"timestamp": 0, "event": "saw Agent B share berries", "impact": -0.3},
    {"timestamp": 5, "event": "felt lonely at fire pit", "impact": 0.5}
  ]
}
```

### Agent State (Updated Every Tick)
```
{
  "agent_id": "Agent1",
  "location": [10, 10],          // Current x, y
  "hunger": 5,                   // 0-10 scale; 0 = death
  "energy": 7,                   // 0-10 scale; 0 = forced to sleep
  "community": 8,                // 0-10 scale; 0 = deep loneliness
  "inventory": ["berry", "berry"]
}
```

---

## WORLD STATE MODEL

```
{
  "tick": 142,
  "locations": {
    "fire_pit": {
      "position": [10, 10],
      "agents_here": ["agent_1", "agent_2"],
      "last_interaction": "agent_1 gave berry to agent_2"
    },
    "berry_bush": {
      "position": [2, 18],
      "berries_available": 15
    },
    "shelter": {
      "position": [18, 2],
      "sleeping_agents": ["agent_3"]
    }
  },
  "chronicle": [
    {"tick": 140, "entry": "Agent 1 and Agent 2 met at fire pit"},
    {"tick": 141, "entry": "Agent 1 gave berry to Agent 2"}
  ]
}
```

---

## THE AUTONOMOUS DECISION LOOP (Per Tick)

For each **awake** agent:

### Step 1: Perception
Gather what the agent can observe:
- Who is at my location?
- How many berries are available nearby?
- What is my current hunger/energy/community level?

### Step 2: Memory Recall
Retrieve the 3-5 most relevant memories:
- "Last interaction with Agent B?"
- "How am I feeling about being alone?"
- "Where did I find food last time?"

### Step 3: LLM Decision Prompt

Send this to an LLM (e.g., GPT-4o-mini, Claude 3.5 Sonnet):

```
You are {AGENT_NAME}, an autonomous agent in a prehistoric village.

PERSONALITY:
- You value social connection (Sociability: {TRAIT_VALUE})
- You tend to be greedy (Greed: {TRAIT_VALUE})
- You are curious about the world (Curiosity: {TRAIT_VALUE})

CURRENT STATE:
- Hunger: {HUNGER}/10 (0 = death, 10 = full)
- Energy: {ENERGY}/10 (0 = must sleep, 10 = energized)
- Community: {COMMUNITY}/10 (0 = lonely, 10 = socially fulfilled)
- Location: {LOCATION_NAME}
- Inventory: {INVENTORY}

WHAT YOU PERCEIVE RIGHT NOW:
- Other agents here: {LIST_OF_AGENTS}
- Resources available: {AVAILABLE_RESOURCES}
- Weather/Environment: {ENVIRONMENT_STATE}

YOUR RECENT MEMORIES:
{MEMORY_LOG}

POSSIBLE ACTIONS:
- MOVE_TO: [fire_pit, berry_bush, shelter] (costs 1 energy)
- FORAGE: Gather berries (costs 1 energy, gains 2 berries)
- EAT: Consume a berry (reduces hunger by 3)
- SLEEP: Rest at shelter (costs 2 energy, gains 5 energy, resets community to 8)
- TALK: Initiate dialogue with another agent
- GIVE_ITEM: Share with another agent
- DO_NOTHING: Rest and observe

Based on your personality and current state, decide your next action.

Respond in this EXACT JSON format:
{
  "thought": "brief internal monologue explaining your decision",
  "action": "ACTION_NAME",
  "parameters": {
    "target_location": "if applicable",
    "target_agent": "if applicable",
    "item": "if applicable",
    "message": "if applicable"
  }
}
```

### Step 4: Action Execution
Parse the LLM response and update the world state:
- If "MOVE_TO": Update agent location, decrease energy by 1.
- If "FORAGE": Add 2 berries to inventory, decrease energy by 1.
- If "EAT": Decrease hunger by 3 (min 0), add memory "I ate a berry."
- If "GIVE_ITEM": Transfer item to another agent, decrease greed affinity.
- If "TALK": Log the interaction and update both agents' community stats.

### Step 5: Natural Decay
- Increase hunger by 1 per tick.
- If energy reaches 0, force agent to move to shelter and sleep.
- If community reaches 0, add a negative affect memory.

---

## CHARACTER CREATION FLOW

When a user wants to create an agent:

1. **Input Name:** e.g., "Kael"
2. **Set Genes:** 
   - Greed slider (0 = altruist, 1 = hoarder)
   - Sociability slider (0 = hermit, 1 = extrovert)
   - Curiosity slider (0 = routine, 1 = explorer)
3. **Initial State:** 
   - Spawn at fire pit with hunger=5, energy=10, community=5
   - Empty inventory
   - Empty memory log
4. **Add to World:** Agent is now active and begins making autonomous decisions.

---

## SUCCESS CRITERIA FOR MVP

- [ ] An agent autonomously chooses to eat when hunger > 7.
- [ ] Two agents meet at the fire pit and their interaction is logged.
- [ ] One agent changes behavior based on a memory of another agent.
- [ ] The simulation runs for 100+ ticks without crashing.
- [ ] A user can create a new agent via a simple CLI/UI and see it appear in the world.

---

## IMPLEMENTATION RECOMMENDATIONS

**Tech Flexibility:**
- Use any language/framework you're comfortable with (Python, Node.js, Rust, Go, etc.).
- For AI integration: Use an API (OpenAI, Anthropic) or a local model (Ollama, LLaMA).
- For storage: Use SQLite, JSON files, or any lightweight database.
- For visualization: Start with a CLI (print a 20x20 grid with emojis), then graduate to a web dashboard.

**Priority Order:**
1. Build the **Agent Decision Loop** (LLM integration).
2. Implement **World State Management** (locations, inventory, stats).
3. Create **Character Creation** (at least via code/config).
4. Build the **Chronicle Logger** (simple text file showing what happened).
5. Add a **CLI Viewer** to visualize agents on the grid.

---

## KEY ARCHITECTURAL PRINCIPLES

1. **Stateless Decisions:** The LLM prompt contains ALL context; the LLM doesn't need to "remember" previous sessions.
2. **Emergent Rules:** Behaviors like "sharing at noon" should emerge from multiple agents' decisions, NOT be hard-coded.
3. **Memory as First-Class:** Agents' memories shape their future decisions; this is the foundation of society-building.
4. **Observable Autonomy:** Every action should be logged and visible to the user. The chronicle is the "proof" of autonomy.

---

## NOW PROCEED WITH BUILDING THE MVP

Using the structure above, create:

1. **World Engine:** Loop that advances ticks and manages agent state.
2. **Agent Decision Maker:** Function that calls the LLM with the above prompt template.
3. **Character Creator:** CLI/UI to let users instantiate new agents.
4. **Logger/Visualizer:** Show the 20x20 grid and the chronicle of events.

Feel free to ask clarifying questions or propose optimizations. The goal is a working **proof of concept** that agents autonomously survive, interact, and remember each other.
