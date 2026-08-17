"""
Ability handler module for triggering passive abilities.

This module provides unified functions for triggering passive abilities
during game actions, eliminating code duplication across reducer functions.
"""

from ptcg.core.ability import PassiveAbility
from ptcg.core.enums import AbilityTrigger
from ptcg.utils.utils import (
    current_active,
    current_all_pokemon,
    current_player,
    is_active_ability_suppressed,
    opponent_all_pokemon,
    opponent_player,
)


def _passive_abilities(card, trigger: AbilityTrigger) -> list[PassiveAbility]:
    """Return passive abilities on a card that match the requested trigger."""
    abilities = getattr(card, "ability", [])
    if not isinstance(abilities, list):
        abilities = [abilities]
    return [
        ability
        for ability in abilities
        if isinstance(ability, PassiveAbility) and ability.abilityTrigger == trigger
    ]


def trigger_passive_ability(card, action, state, trigger: AbilityTrigger) -> None:
    """
    Trigger a card's passive ability if it matches the given trigger.

    Args:
        card: The card to check for ability
        action: The action being performed
        state: Current game state
        trigger: The ability trigger type to match
    """
    handler = getattr(card, "use_ability", None)
    if not callable(handler):
        return

    for ability in _passive_abilities(card, trigger):
        handler(action, state)
        ability_name = ability.name if ability.name else "Unknown"
        card_name = card.name if hasattr(card, "name") else "Unknown"
        state.auto_events.append(f"Passive ability triggered: {card_name}'s {ability_name}.")


def trigger_attack_abilities(action, state) -> None:
    """
    Trigger all passive abilities related to an attack action.

    This includes:
    - Source Pokemon's ATTACKING abilities
    - Source's attachments' ATTACKING abilities
    - Target's attachments' ATTACKED abilities
    - Opponent Pokemon's ATTACKED abilities
    - Stadium's ATTACKING abilities

    Args:
        action: The AttackAction or EffectAction being performed
        state: Current game state
    """
    # Trigger the attacking side's in-play abilities. Opposing effects such as
    # Midnight Fluttering suppress only the Active Pokemon's abilities.
    source_player = current_player(state)
    source_active_suppressed = is_active_ability_suppressed(source_player, state)
    for card in current_all_pokemon(state):
        if source_active_suppressed and card in source_player.active:
            continue
        trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKING)

    # Trigger source's attachments' ATTACKING abilities
    for card in action.source.attachment:
        trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKING)

    # Trigger target's attachments' ATTACKED abilities
    if hasattr(action, "target"):
        for card in action.target.attachment:
            trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKED)

    # Trigger opponent Pokemon's ATTACKED abilities, respecting suppression of
    # the opponent's Active Pokemon while leaving Benched abilities available.
    target_player = opponent_player(state)
    target_active_suppressed = is_active_ability_suppressed(target_player, state)
    for card in opponent_all_pokemon(state):
        if target_active_suppressed and card in target_player.active:
            continue
        trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKED)

    # Trigger stadium's ATTACKING abilities
    for card in state.stadium:
        trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKING)


def trigger_retreat_abilities(action, state) -> None:
    """
    Trigger all passive abilities related to a retreat action.

    This includes:
    - Active Pokemon's RETREAT ability
    - Active Pokemon's attachments' RETREAT abilities
    - Stadium's RETREAT abilities

    Args:
        action: The RetreatAction being performed
        state: Current game state
    """
    current_active_pokemon = current_active(state)[0]

    # Trigger active Pokemon's RETREAT ability
    trigger_passive_ability(current_active_pokemon, action, state, AbilityTrigger.RETREAT)

    # Trigger attachments' RETREAT abilities
    for card in current_active_pokemon.attachment:
        trigger_passive_ability(card, action, state, AbilityTrigger.RETREAT)

    # Trigger stadium's RETREAT abilities
    for card in state.stadium:
        trigger_passive_ability(card, action, state, AbilityTrigger.RETREAT)
