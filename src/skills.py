"""
Skill system — pluggable agent actions.

To add a new skill:
  1. Create a class inheriting from Skill.
  2. Implement validate() and execute().
  3. Register it at the bottom: SKILL_REGISTRY.register(MySkill())

No other file needs to change for the new skill to be available in
prompts, validated, and executed during the tick loop.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .environment import Environment
    from .storage import StorageBackend


class Skill(ABC):
    """Base class for all agent actions.

    Attributes:
        name:               Action keyword returned by the LLM (uppercase).
        prompt_description: One-line description shown in the agent prompt.
    """

    name: str = ""
    prompt_description: str = ""

    @abstractmethod
    def validate(
        self,
        agent: dict,
        target: str,
        message: str,
        agents: list[dict],
        resource_state: dict[str, int],
        env: "Environment",
    ) -> bool:
        """Return True if this skill can be executed in the current context."""
        ...

    @abstractmethod
    def execute(
        self,
        agent: dict,
        target: str,
        message: str,
        agents: list[dict],
        resource_state: dict[str, int],
        env: "Environment",
        tick: int,
        storage: "StorageBackend",
    ) -> None:
        """Execute the skill, writing side-effects through storage."""
        ...


class SkillRegistry:
    """
    Central registry of all available agent skills.
    Skills are looked up by action name (case-insensitive).
    """

    def __init__(self) -> None:
        self._registry: dict[str, Skill] = {}

    def register(self, skill: Skill) -> "SkillRegistry":
        self._registry[skill.name.upper()] = skill
        return self

    def get(self, name: str) -> Skill | None:
        return self._registry.get(name.upper())

    def names(self) -> list[str]:
        return list(self._registry.keys())

    def prompt_lines(self) -> list[str]:
        return [s.prompt_description for s in self._registry.values()]


# ---------------------------------------------------------------------------
# Skill implementations
# ---------------------------------------------------------------------------

class MoveSkill(Skill):
    name = "MOVE_TO"
    prompt_description = "MOVE_TO    — target: location name"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        return target in env.location_names() and agent["energy"] > 0

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        storage.update_agent(agent["id"], location=target)
        storage.add_memory(agent["id"], tick, f"Moved to {target}")
        storage.add_chronicle(
            tick, f"{agent['name']} walked to {target.replace('_', ' ')}", "MOVE", agent["id"]
        )


class ForageSkill(Skill):
    name = "FORAGE"
    prompt_description = "FORAGE     — harvest resource at current location, costs 1 energy"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        if agent["energy"] <= 0:
            return False
        return any(
            agent["location"] in r.harvest_locations and resource_state.get(r.name, 0) > 0
            for r in env.resources.values()
        )

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        inventory = json.loads(agent["inventory"])
        for res in env.resources.values():
            if agent["location"] not in res.harvest_locations:
                continue
            available = resource_state.get(res.name, 0)
            if available <= 0:
                continue
            actual = min(res.harvest_yield, available)
            inventory.extend([res.name] * actual)
            storage.update_agent(
                agent["id"],
                inventory=json.dumps(inventory),
                energy=max(0, agent["energy"] - 1),
            )
            storage.adjust_resource(res.name, -actual)
            storage.add_memory(agent["id"], tick, f"Foraged {actual} {res.name} {res.icon}")
            storage.add_chronicle(
                tick,
                f"{agent['name']} foraged {actual} {res.name} {res.icon}",
                "FORAGE",
                agent["id"],
            )
            break  # one resource type per forage action


class EatSkill(Skill):
    name = "EAT"
    prompt_description = "EAT        — consume food item from inventory"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        inventory = json.loads(agent["inventory"])
        food_items = env.food_items()
        return any(item in food_items for item in inventory)

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        inventory = json.loads(agent["inventory"])
        food_items = env.food_items()
        for item in inventory:
            if item in food_items:
                res = env.resources[item]
                inventory.remove(item)
                storage.update_agent(
                    agent["id"],
                    inventory=json.dumps(inventory),
                    hunger=min(10, agent["hunger"] + res.hunger_value),
                )
                storage.add_memory(agent["id"], tick, f"Ate {item} {res.icon} — hunger relieved")
                storage.add_chronicle(
                    tick, f"{agent['name']} is eating {item} {res.icon}", "EAT", agent["id"]
                )
                break


class SleepSkill(Skill):
    name = "SLEEP"
    prompt_description = "SLEEP      — rest; +5 energy at shelter, +2 anywhere"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        return True  # Always valid

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        gain = 5 if agent["location"] == "shelter" else 2
        storage.update_agent(agent["id"], energy=min(10, agent["energy"] + gain))
        storage.add_memory(agent["id"], tick, f"Rested at {agent['location']} (+{gain} energy)")
        storage.add_chronicle(
            tick,
            f"{agent['name']} is sleeping/resting at {agent['location']}",
            "SLEEP",
            agent["id"],
        )


class TalkSkill(Skill):
    name = "TALK"
    prompt_description = "TALK       — target: agent name at same location, message: short speech"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        if not target or not message:
            return False
        return any(
            a["name"].lower() == target.lower() and a["location"] == agent["location"]
            for a in agents
            if a["id"] != agent["id"]
        )

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        tgt = next(
            (
                a for a in agents
                if a["name"].lower() == target.lower() and a["location"] == agent["location"]
            ),
            None,
        )
        if not tgt:
            return
        storage.update_agent(agent["id"], community=min(10, agent["community"] + 2))
        storage.update_agent(tgt["id"], community=min(10, tgt["community"] + 1))
        storage.add_memory(
            agent["id"], tick,
            f'Spoke to {tgt["name"]}: "{message[:60]}"',
            target=tgt["name"], message=message,
        )
        storage.add_memory(
            tgt["id"], tick,
            f'{agent["name"]} said: "{message[:60]}"',
            target=agent["name"], message=message,
        )
        storage.add_chronicle(
            tick,
            f'💬 {agent["name"]} → {tgt["name"]}: "{message[:120]}"',
            "TALK",
            agent["id"],
        )


class GiveBerrySkill(Skill):
    name = "GIVE_BERRY"
    prompt_description = "GIVE_BERRY — target: agent name at same location (gives one food item)"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        if not target:
            return False
        inventory = json.loads(agent["inventory"])
        food_items = env.food_items()
        if not any(item in food_items for item in inventory):
            return False
        return any(
            a["name"].lower() == target.lower() and a["location"] == agent["location"]
            for a in agents
            if a["id"] != agent["id"]
        )

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        tgt = next(
            (
                a for a in agents
                if a["name"].lower() == target.lower() and a["location"] == agent["location"]
            ),
            None,
        )
        if not tgt:
            return
        inventory = json.loads(agent["inventory"])
        food_items = env.food_items()
        item_to_give = next((item for item in inventory if item in food_items), None)
        if not item_to_give:
            return
        inventory.remove(item_to_give)
        t_inv = json.loads(tgt["inventory"])
        t_inv.append(item_to_give)
        storage.update_agent(agent["id"], inventory=json.dumps(inventory))
        storage.update_agent(tgt["id"], inventory=json.dumps(t_inv))
        storage.add_memory(agent["id"], tick, f'Gave {item_to_give} to {tgt["name"]}')
        storage.add_memory(tgt["id"], tick, f'{agent["name"]} gave me {item_to_give} 🎁')
        storage.add_chronicle(
            tick,
            f'🎁 {agent["name"]} gave {item_to_give} to {tgt["name"]}',
            "GIVE_BERRY",
            agent["id"],
        )


class DoNothingSkill(Skill):
    name = "DO_NOTHING"
    prompt_description = "DO_NOTHING"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        return True

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        pass  # Intentionally empty


# ---------------------------------------------------------------------------
# Default registry — populated at import time.
# To add a new skill: create a Skill subclass and call register() below.
# ---------------------------------------------------------------------------
SKILL_REGISTRY = SkillRegistry()
SKILL_REGISTRY.register(MoveSkill())
SKILL_REGISTRY.register(ForageSkill())
SKILL_REGISTRY.register(EatSkill())
SKILL_REGISTRY.register(SleepSkill())
SKILL_REGISTRY.register(TalkSkill())
SKILL_REGISTRY.register(GiveBerrySkill())
SKILL_REGISTRY.register(DoNothingSkill())
