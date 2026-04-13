# Loka: Technical Architecture Plan

This document outlines the high-level architecture for **Loka**, a virtual world where AI agents and human players collaborate to build a society.

## 1. System Overview
The architecture is divided into four primary layers:
1.  **Simulation Layer:** The "Engine" that maintains the world state and time.
2.  **Cognitive Layer:** The "Brain" of the AI agents.
3.  **Interaction Layer:** The "Social Fabric" enabling communication and economy.
4.  **Interface Layer:** The "Window" through which humans interact with the world.

---

## 2. Component Breakdown

### A. Simulation Layer (The World)
- **State Engine:** A central service (Node.js/Go/Python) that tracks the position and status of every entity.
- **Temporal Loop:** A tick-based system that advances world time and triggers agent updates.
- **Spatial Awareness:** A grid or region-based system to handle local interactions efficiently.

### B. Cognitive Layer (The Agents)
- **Persona Engine:** Defines traits, goals, and backgrounds for each agent.
- **Memory Stream:** (Vector DB) Stores past interactions and observations.
- **Reasoning Loop:** 
    - **Perception:** What do I see/hear?
    - **Reflection:** What does this mean for me?
    - **Planning:** What should I do next?
    - **Action:** How do I execute it?

### C. Interaction Layer (Society)
- **Dialogue System:** LLM-driven natural language interaction between agents and players.
- **Social Graph:** Tracking reputations, friendships, and hierarchies.
- **Resource Management:** A basic economy (trading, gathering, building) to drive social needs.

### D. Interface Layer (The Players)
- **Avatar System:** Customizable characters for human users.
- **Real-time Visualization:** (Three.js or Unity) Rendering the world state for the browser or desktop.
- **API Gateway:** Secure connection between the client and the simulation.

---

## 3. Technology Stack Suggestions
| Component | Technology |
| :--- | :--- |
| **Logic/Backend** | Node.js (TypeScript) or Python (FastAPI) |
| **AI / LLM** | OpenAI API / Anthropic / Local LLMs (Ollama) |
| **Memory Storage** | Pinecone, Milvus, or Weaviate |
| **World Persistence** | PostgreSQL (Relational) + Redis (Real-time) |
| **Frontend** | React + Three.js (R3F) |

---

## 4. Immediate Next Steps
1.  **Define the "Tiny World" Scope:** Start with a single village or room.
2.  **Select LLM Architecture:** Choose between a central LLM or local models for agents.
3.  **Prototype Agent Memory:** Implement a basic reflect-and-store loop.
