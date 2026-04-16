"""
Configuration constants for the simulation.
"""

# Agent Stats
MAX_STAT_VALUE = 10
HUNGER_THRESHOLD_LOW = 5
ENERGY_THRESHOLD_LOW = 5
DANGER_THRESHOLD = 2

# Resource Balancing
DEFAULT_BERRY_MAX = 1
DEFAULT_BERRY_REGEN = 1
DEFAULT_BERRY_YIELD = 1
DEFAULT_BERRY_HUNGER = 3

# Simulation Intervals
DEFAULT_TICK_INTERVAL = 5
MEMORY_WINDOW_LIMIT = 20
CHRONICLE_LIMIT = 30

# Energy Gains
ENERGY_GAIN_SHELTER = 5
ENERGY_GAIN_ANYWHERE = 2

# Game Rules & Objectives
WIN_CONDITION_GOLD = 30
INHERITANCE_ENABLED = True

# Behavioral Framework (Descriptive, not Prescriptive)
GAME_RULES = f"THE GAME: Your absolute goal is to accumulate {WIN_CONDITION_GOLD} Gold coins. Survival is the prerequisite. If you die, your wealth is equally distributed among the survivors. There are no other rules. You define your own morality and strategy."
SOCIAL_STATUS_GUIDELINE = "Social Bar (Community) is your Loka Identity. 0-3 = ISOLATED, 4-6 = STABLE, 7-10 = INFLUENTIAL. This affects how others perceive your value as a trade partner or ally."
REASONING_REINFORCEMENT = """Your 'thought' MUST follow this Strategic Planning Template:
1. SITUATION: Analysis of your current stats, gold, and immediate surroundings.
2. STRATEGY: Your long-term plan to reach 30 Gold (e.g., 'Monopolize resources', 'Build trade alliances', 'Wait for inheritance').
3. EXECUTION: The specific steps you are taking in this tick to advance your strategy."""

