"""
Ability handler module for triggering passive abilities.

This module provides unified functions for triggering passive abilities
during game actions, eliminating code duplication across reducer functions.
"""

from ptcg.core.ability import PassiveAbility
from ptcg.core.enums import AbilityTrigger
from ptcg.utils.utils import (
    current_active,
    current_player,
    is_active_ability_suppressed,
    opponent_all_pokemon,
)


def _has_passive_ability(card, trigger: AbilityTrigger) -> bool:
    """Check if a card has a passive ability with the given trigger."""
    return (
        hasattr(card, "ability")
        and isinstance(getattr(card, "ability"), PassiveAbility)
        and card.ability.abilityTrigger == trigger
    )


def trigger_passive_ability(card, action, state, trigger: AbilityTrigger) -> None:
    """
    Trigger a card's passive ability if it matches the given trigger.

    Args:
        card: The card to check for ability
        action: The action being performed
        state: Current game state
        trigger: The ability trigger type to match
    """
    if _has_passive_ability(card, trigger):
        card.use_ability(action, state)
        ability_name = card.ability.name if hasattr(card.ability, "name") else "Unknown"
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
    # Trigger source's ATTACKING ability (unless suppressed by opponent's active, e.g., Midnight Fluttering)
    source_player = current_player(state)
    if not is_active_ability_suppressed(source_player, state):
        trigger_passive_ability(action.source, action, state, AbilityTrigger.ATTACKING)

    # Trigger source's attachments' ATTACKING abilities
    for card in action.source.attachment:
        trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKING)

    # Trigger target's attachments' ATTACKED abilities
    if hasattr(action, "target"):
        for card in action.target.attachment:
            trigger_passive_ability(card, action, state, AbilityTrigger.ATTACKED)

    # Trigger opponent Pokemon's ATTACKED abilities
    for card in opponent_all_pokemon(state):
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
