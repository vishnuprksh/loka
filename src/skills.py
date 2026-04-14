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

from .config import MAX_STAT_VALUE, ENERGY_GAIN_SHELTER, ENERGY_GAIN_ANYWHERE


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
                    hunger=min(MAX_STAT_VALUE, agent["hunger"] + res.hunger_value),
                )
                storage.add_memory(agent["id"], tick, f"Ate {item} {res.icon} — hunger relieved")
                storage.add_chronicle(
                    tick, f"{agent['name']} is eating {item} {res.icon}", "EAT", agent["id"]
                )
                break


class SleepSkill(Skill):
    name = "SLEEP"
    prompt_description = "SLEEP      — rest; +10 energy at shelter, +4 anywhere"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        return True  # Always valid

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        gain = ENERGY_GAIN_SHELTER if agent["location"] == "shelter" else ENERGY_GAIN_ANYWHERE
        storage.update_agent(agent["id"], energy=min(MAX_STAT_VALUE, agent["energy"] + gain))
        storage.add_memory(agent["id"], tick, f"Rested at {agent['location']} (+{gain} energy)")
        storage.add_chronicle(
            tick,
            f"{agent['name']} is sleeping/resting at {agent['location']}",
            "SLEEP",
            agent["id"],
        )


class TalkSkill(Skill):
    name = "TALK"
    prompt_description = "TALK       — target: agent name at same location (or 'everyone'), message: short speech"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        if not target or not message:
            return False
        if target.lower() == "everyone":
            return any(a["id"] != agent["id"] and a["location"] == agent["location"] for a in agents)
            
        return any(
            a["name"].lower() == target.lower() and a["location"] == agent["location"]
            for a in agents
            if a["id"] != agent["id"]
        )

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        location = agent["location"]
        is_shout = target.lower() == "everyone"
        
        # Agents present at the location (excluding the speaker)
        listeners = [
            a for a in agents
            if a["id"] != agent["id"] and a["location"] == location
        ]
        
        if not listeners:
            return

        # Target specific listener if not a shout
        tgt_agent = None
        if not is_shout:
            tgt_agent = next(
                (a for a in listeners if a["name"].lower() == target.lower()),
                None
            )
            if not tgt_agent:
                return

        # Clear all pending unanswered messages for the caller as they are now responding/starting a turn
        conn = storage.get_conn()
        with conn:
            conn.execute("UPDATE memories SET is_unanswered=0 WHERE agent_id=?", (agent["id"],))
        conn.close()

        # Update relationships
        # Speaker and listeners get a minor boost for interaction
        # We process broadcast differently from direct speech
        
        # Add memory for the speaker
        target_name = "Everyone" if is_shout else tgt_agent["name"]
        storage.add_memory(
            agent["id"], tick,
            f'Spoke to {target_name}: "{message[:60]}"',
            target=target_name, message=message,
            location=location
        )
        
        # Broadcast to all listeners
        for listener in listeners:
            # Relationship update: Listener likes speaker slightly more (+1) for talking
            storage.update_relationship(agent["id"], listener["id"], 1)
            
            # Listener's memory: indicates who said what and the target
            is_target = (not is_shout and listener["id"] == tgt_agent["id"])
            if is_target:
                status_text = f'{agent["name"]} said to you: "{message[:60]}"'
                is_unanswered = 1
            else:
                target_hint = "everyone" if is_shout else tgt_agent["name"]
                status_text = f'{agent["name"]} (at {location}) said to {target_hint}: "{message[:60]}"'
                is_unanswered = 0
            
            storage.add_memory(
                listener["id"], tick,
                status_text,
                target=(agent["name"] if is_target else target_name), 
                message=message,
                is_unanswered=is_unanswered,
                location=location
            )
        
        # Add to global chronicle
        target_display = "everyone" if is_shout else tgt_agent["name"]
        storage.add_chronicle(
            tick,
            f'💬 {agent["name"]} → {target_display}: "{message[:120]}"',
            "TALK",
            agent["id"],
        )


class GiveBerrySkill(Skill):
    name = "GIVE_BERRY"
    prompt_description = "GIVE_BERRY — target: agent name at same location (for free sharing with allies who ASKED for food)"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        if not target:
            return False
        inventory = json.loads(agent["inventory"])
        food_items = env.food_items()
        if not any(item in food_items for item in inventory):
            return False
        
        # Check if the target is present
        target_agent = next(
            (a for a in agents if a["name"].lower() == target.lower() and a["location"] == agent["location"]),
            None
        )
        if not target_agent:
            return False

        # MANDATORY COMMUNICATION: Target must have asked for food/berries in their last message
        from .storage import SQLiteBackend
        storage = SQLiteBackend() # The tick loop provides storage, but validate doesn't. 
        # Actually, let's just check the memories passed via 'agents' if possible? No, we need fresh DB check.
        # Check if there is an unread message from this target to the agent containing keywords.
        memories = storage.get_recent_memories(agent["id"], limit=5)
        for m in memories:
            if m.get("target") == agent["name"] and m.get("is_unanswered"):
                msg = (m.get("message") or "").lower()
                if any(word in msg for word in ["food", "berry", "berries", "hungry", "starving", "give", "help"]):
                    return True
        
        return False

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
        
        # New Relationship logic: Target significantly likes donor (+5)
        # Donor likes target slightly for being helpful (+1)
        storage.update_relationship(agent["id"], tgt["id"], 5)
        storage.update_relationship(tgt["id"], agent["id"], 1)

        storage.add_memory(agent["id"], tick, f'Gave {item_to_give} to {tgt["name"]}')
        storage.add_memory(tgt["id"], tick, f'{agent["name"]} gave me {item_to_give} 🎁')
        storage.add_chronicle(
            tick,
            f'🎁 {agent["name"]} gave {item_to_give} to {tgt["name"]}',
            "GIVE_BERRY",
            agent["id"],
        )


class PaySkill(Skill):
    name = "PAY"
    prompt_description = "PAY        — target: agent name at same location, message: amount (integer)"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        try:
            amount = int(message)
            if amount <= 0:
                return False
        except ValueError:
            return False

        if agent.get("money", 0) < amount:
            return False

        return any(
            a["name"].lower() == target.lower() and a["location"] == agent["location"]
            for a in agents
            if a["id"] != agent["id"]
        )

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        try:
            amount = int(message)
        except ValueError:
            return

        target_agent = next(
            (a for a in agents if a["name"].lower() == target.lower() and a["location"] == agent["location"]),
            None
        )
        if not target_agent:
            return

        # Transfer money
        storage.update_agent(agent["id"], money=agent["money"] - amount)
        storage.update_agent(target_agent["id"], money=target_agent["money"] + amount)

        # Update relationships: Recipient likes payer (+1 per 5 gold, min 1)
        rel_boost = max(1, amount // 5)
        storage.update_relationship(agent["id"], target_agent["id"], rel_boost)

        # Update memories
        storage.add_memory(agent["id"], tick, f"Paid {amount} gold to {target_agent['name']}")
        storage.add_memory(target_agent["id"], tick, f"Received {amount} gold from {agent['name']}")
        
        storage.add_chronicle(
            tick,
            f"💰 {agent['name']} paid {amount} gold to {target_agent['name']}",
            "PAY",
            agent["id"],
        )


class OfferForSaleSkill(Skill):
    name = "OFFER_FOR_SALE"
    prompt_description = "OFFER_FOR_SALE — target: item name, message: price (e.g. 'Selling berry for 15 gold' — use high prices for unlikable people)"

    def validate(self, agent, target, message, agents, resource_state, env) -> bool:
        inventory = json.loads(agent["inventory"])
        # target should be the item name
        return target.lower() in [i.lower() for i in inventory]

    def execute(self, agent, target, message, agents, resource_state, env, tick, storage) -> None:
        # This is primarily a social signal stored in memory and chronicle
        storage.add_memory(agent["id"], tick, f"Offered {target} for sale: {message}")
        
        # Notify others at the location
        for a in agents:
            if a["location"] == agent["location"] and a["id"] != agent["id"]:
                storage.add_memory(a["id"], tick, f"{agent['name']} is selling {target}: {message}")

        storage.add_chronicle(
            tick,
            f"📢 {agent['name']} offered {target} for sale: {message}",
            "TRADE",
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
SKILL_REGISTRY.register(PaySkill())
SKILL_REGISTRY.register(OfferForSaleSkill())
SKILL_REGISTRY.register(DoNothingSkill())
