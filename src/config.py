"""
Configuration constants for the simulation.
"""

# Agent Stats
MAX_STAT_VALUE = 10
HUNGER_THRESHOLD_LOW = 5
ENERGY_THRESHOLD_LOW = 5

# Resource Balancing
DEFAULT_BERRY_MAX = 1
DEFAULT_BERRY_REGEN = 1
DEFAULT_BERRY_YIELD = 1
DEFAULT_BERRY_HUNGER = 4

# Simulation Intervals
DEFAULT_TICK_INTERVAL = 5
MEMORY_WINDOW_LIMIT = 20
CHRONICLE_LIMIT = 30

# Energy Gains
ENERGY_GAIN_SHELTER = 5
ENERGY_GAIN_ANYWHERE = 2

# Behavioral Guidelines
SURVIVAL_GUIDELINE = "SURVIVAL IS YOUR ABSOLUTE PRIORITY. Every tick you lose 1 Fullness and 1 Rest. If either hits 0, you PERISH. You can now perform multiple actions in one tick (e.g., EAT and TALK). Think 5-10 ticks ahead: do you have enough food in your inventory? Are you near a shelter to rest? Do not wait until you are starving to act."
SOCIAL_STATUS_GUIDELINE = "Social Bar (Community) is your Loka Identity. 0-3 = ISOLATED (Depression, others may ignore you), 4-6 = STABLE (A face in the crowd), 7-10 = INFLUENTIAL (People listen to you, trading is easier). This bar is VISIBLE to everyone."
PRIMITIVE_ECONOMY_GUIDELINE = "SOCIAL SHARING & HUNGER: If you are hungry, ASK for food via TALK. If you have extra food, SHARE it freely (GIVE_BERRY) with those you like (High Relationship score). For those you dislike or don't know well, SELL items at a higher price (OFFER_FOR_SALE + PAY) to build a Gold buffer for your own future survival. Sharing for free to unlikable people is considered foolishness."
REASONING_REINFORCEMENT = "Before acting, perform a SITUATIONAL ANALYSIS in your 'thought' field: Evaluate your current survival buffer, assess your social standing, and decide if you are playing it too safe or taking too many risks."
