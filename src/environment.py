"""
Environment definition — locations and resources in the world.

To extend the world:
  - Add a new Location to THE_GROVE.locations
  - Add a new Resource to THE_GROVE.resources

No other file needs to change for discovery and prompting.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Location:
    """A named place agents can move to."""
    name: str
    x: int
    y: int


@dataclass
class Resource:
    """A harvestable, consumable resource in the world.

    Attributes:
        name:               Identifier used in inventory and DB (keep singular, lowercase).
        max_count:          Maximum units that can exist in the world at once.
        regen_per_tick:     Units regenerated each tick.
        harvest_locations:  Location names where agents can FORAGE this resource.
        harvest_yield:      Units obtained per FORAGE action.
        hunger_value:       Hunger restored when an agent EATs one unit (0 = not food).
        icon:               Emoji used in log messages.
    """
    name: str
    max_count: int
    regen_per_tick: int
    harvest_locations: list[str]
    harvest_yield: int = 1
    hunger_value: int = 0
    icon: str = "📦"


class Environment:
    """
    Defines the physical world: its named locations and available resources.
    Skills and the simulation engine depend only on this interface, so new
    locations or resources propagate automatically without touching core logic.
    """

    def __init__(
        self,
        name: str,
        locations: dict[str, Location],
        resources: dict[str, Resource],
    ) -> None:
        self.name = name
        self.locations = locations
        self.resources = resources

    def location_names(self) -> list[str]:
        return list(self.locations.keys())

    def resource_names(self) -> list[str]:
        return list(self.resources.keys())

    def harvestable_at(self, location_name: str) -> list[Resource]:
        """Return resources harvestable at a given location."""
        return [
            r for r in self.resources.values()
            if location_name in r.harvest_locations
        ]

    def food_items(self) -> list[str]:
        """Return resource names that restore hunger when consumed."""
        return [r.name for r in self.resources.values() if r.hunger_value > 0]


# ---------------------------------------------------------------------------
# Default world: "The Grove"
# Add locations/resources here — they propagate to prompts, skills, and DB.
# ---------------------------------------------------------------------------
THE_GROVE = Environment(
    name="The Grove",
    locations={
        "fire_pit":   Location("fire_pit",   x=10, y=10),
        "berry_bush": Location("berry_bush", x=3,  y=16),
        "shelter":    Location("shelter",    x=17, y=3),
    },
    resources={
        "berry": Resource(
            name="berry",
            max_count=20,
            regen_per_tick=1,
            harvest_locations=["berry_bush"],
            harvest_yield=2,
            hunger_value=3,
            icon="🫐",
        ),
    },
)
