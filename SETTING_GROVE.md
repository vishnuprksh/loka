# Loka: Simple World Setting - "The Grove"

To build the foundation of our AI society, we will start with an extremely simple environment that focuses on **Social Interaction** and **Resource Tension**.

## 1. The Environment: "The Grove"
- **Setting:** A small, secluded clearing in a prehistoric forest.
- **Format:** A 2D Grid (e.g., 20x20 tiles).
- **Points of Interest:**
    - **The Fire Pit:** (Center) Provides warmth and serves as the primary social hub.
    - **The Berry Bushes:** (Perimeter) The only source of food.
    - **The Shelter:** (Edge) Where agents must go to "rest" (save state/sleep).

---

## 2. The Core Mechanic: Survival & Socializing
Agents have three primary "Needs":
1.  **Hunger:** Decreases over time. Replenished by foraging berries.
2.  **Energy:** Decreased by moving/acting. Replenished by sleeping at the Shelter.
3.  **Community:** Decreased by isolation. Replenished by talking to others near the Fire Pit.

---

## 3. Initial Social Roles
To create tension and growth, each agent will be assigned a simple "Drive":
- **The Provider:** Focused on gathering and sharing berries.
- **The Storyteller:** Focused on talking and keeping "Community" high.
- **The Builder:** Focused on maintaining the Fire Pit.

---

## 4. Why This Setting?
- **Social Over Space:** With only a few locations, agents spend more time interacting than navigating.
- **Observable Hierarchy:** Who gets to eat first? Who keeps the fire going? This creates the first "Rules" of their society.
- **Low Barrier to Entry:** We can represent this with simple emojis or sprites (🔥, 🫐, 🛌, 🧙) while focusing the backend on the LLM brain.

---

## 5. First Proto-Rules (The "Loka Code")
1.  **Must Eat:** If Hunger = 0, agent "leaves" the grove (deletion).
2.  **Shared Memory:** Agents will talk about who brought berries the day before.
3.  **Human Presence:** You enter as "The Visitor" (Avatar) to see how they react to a new member.
