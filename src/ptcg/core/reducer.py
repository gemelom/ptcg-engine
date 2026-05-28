"""
State transition reducers for PTCG game actions.

This module implements the reducer pattern using Python generators
for handling multi-step player interactions (e.g., card selection).

Generator Pattern:
    - yield (obs, reward, done, info): Pause for player input
    - yield from: Delegate to sub-generators
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Generator, List, Tuple, cast

from loguru import logger

from ptcg.core.ability_handler import trigger_attack_abilities, trigger_retreat_abilities
from ptcg.core.action import (
    AttachEnergyAction,
    ChooseCardAction,
    ChooseCardPrompt,
    EffectAction,
    EvolvePokemonAction,
    PlayPokemonAction,
    RetreatAction,
    choose_card_actions,
)
from ptcg.core.enums import CardPosition, PlayerId, PokemonPosition, SuperType
from ptcg.core.exceptions import CardPlayError, GameTermination, InvalidCardPositionError
from ptcg.utils.utils import (
    current_active,
    current_player,
    discard_pokemon,
    move_cards,
    move_pokemon,
    next_turn,
    opponent_player,
    retreat_combinations,
    switch_pokemon,
)

if TYPE_CHECKING:
    from ptcg.core.action import AttackAction
    from ptcg.core.card import Card, EnergyCard, PokemonCard
    from ptcg.core.player import Player
    from ptcg.core.state import State


# =============================================================================
# Constants
# =============================================================================

RESISTANCE_VALUE = 30
DAMAGE_COUNTER_MULTIPLIER = 10


# =============================================================================
# Type Aliases
# =============================================================================

# Generator that yields (obs, reward, done, info) and receives ChooseCardAction
StepGenerator = Generator[Tuple["State", float, bool, dict], ChooseCardAction, None]


# =============================================================================
# Helper Functions
# =============================================================================


def _calculate_damage(
    source: "PokemonCard", target: "PokemonCard", base_damage: int, state: "State"
) -> int:
    """Calculate damage after applying weakness and resistance.

    Args:
        source: The attacking Pokemon card.
        target: The defending Pokemon card.
        base_damage: The base damage value.
        state: Current game state (for recording auto events).

    Returns:
        Final damage after modifiers.
    """
    if source.cardType in target.weakness:
        final = base_damage * 2
        state.auto_events.append(f"Weakness applied: damage doubled from {base_damage} to {final}.")
        return final
    elif source.cardType in target.resistance:
        final = max(0, base_damage - RESISTANCE_VALUE)
        state.auto_events.append(
            f"Resistance applied: damage reduced by {RESISTANCE_VALUE} "
            f"from {base_damage} to {final}."
        )
        return final
    return base_damage


def _force_active_replacement(
    opponent: "Player",
    state: "State",
    original_turn: "PlayerId",
) -> StepGenerator:
    """Force opponent to choose a new active Pokemon from bench.

    Temporarily switches turn to opponent for the choice, then restores.

    Args:
        opponent: The player who must choose a new active.
        state: Current game state.
        original_turn: The player ID to restore after choice.

    Yields:
        (obs, reward, done, info) for card selection.

    Raises:
        GameTermination: If opponent has no benched Pokemon.
    """
    if len(opponent.bench) == 0:
        raise GameTermination

    state.turn = opponent.id
    tips = "Your active Pokemon is knocked out. You have to choose 1 of your benched Pokemon and switch it to your active spot."
    # source param accepts Player for "who is choosing" context
    actions = choose_card_actions(opponent.id, opponent.id, 1, 1, opponent.bench, tips=tips)
    chosen_card = yield from reduce_choose_card_actions(actions, state)
    chosen_card = chosen_card[0]
    move_pokemon(opponent, chosen_card)

    state.turn = original_turn


def _handle_knockout(
    target: "PokemonCard",
    attacker: "Player",
    opponent: "Player",
    state: "State",
) -> StepGenerator:
    """Handle Pokemon knockout: discard, prize selection, and replacement.

    This handles the complete knockout flow:
    1. Discard the knocked out Pokemon
    2. Mark opponent as having a dead Pokemon
    3. Let attacker choose prize cards
    4. Check for game termination (all prizes taken)
    5. If active was knocked out, force replacement

    Args:
        target: The knocked out Pokemon.
        attacker: The player who dealt the knockout.
        opponent: The player who lost their Pokemon.
        state: Current game state.

    Yields:
        (obs, reward, done, info) for card selections.

    Raises:
        GameTermination: If game ends (all prizes or no Pokemon).
    """
    is_active_dead = target.position == PokemonPosition.ACTIVE

    # Allow on_knocked_out tool effects to run before the pokemon is discarded
    for card in list(target.attachment):
        if hasattr(card, "on_knocked_out"):
            yield from card.on_knocked_out(target, is_active_dead, attacker, opponent, state)

    discard_pokemon(opponent, target)
    opponent.hasPokemonDead = True

    # Record knockout event
    target_name = target.name if hasattr(target, "name") else "Pokemon"
    state.auto_events.append(f"{target_name} was knocked out.")

    # Prize card selection
    prize_count = min(len(attacker.prize), target.prize)
    tips = (
        f"Congratulations! You may choose {prize_count} prize card(s) and put them into your hand."
    )
    attacker.reward.apply_prize_card_reward(prize_count)

    actions = choose_card_actions(
        attacker.id,
        attacker.id,
        prize_count,
        prize_count,
        attacker.prize,
        hidden=True,
        tips=tips,
    )
    chosen_card = yield from reduce_choose_card_actions(actions, state)
    move_cards(
        chosen_card,
        (attacker.id, CardPosition.PRIZE),
        (attacker.id, CardPosition.HAND),
        state,
    )

    # Record prize card event
    state.auto_events.append(f"{prize_count} prize card(s) taken.")

    # Check if all prize cards taken - game ends
    if len(attacker.prize) == 0:
        raise GameTermination

    # If active Pokemon was knocked out, opponent must choose replacement
    if is_active_dead:
        yield from _force_active_replacement(opponent, state, attacker.id)


# =============================================================================
# Action Reducers
# =============================================================================


def reduce_attack_action(
    action: "AttackAction",
    state: "State",
    auto_end_turn: bool = True,
) -> StepGenerator:
    """Reduce an attack action.

    Handles damage calculation with weakness/resistance, knockout logic,
    prize card selection, and turn management.

    Args:
        action: The attack action to process.
        state: Current game state.
        auto_end_turn: Whether to end turn after attack (default True).

    Yields:
        (obs, reward, done, info) for any card selections needed.
    """
    trigger_attack_abilities(action, state)
    player = current_player(state)
    opponent = opponent_player(state)

    # action.target is typed as Card in action.py but is always PokemonCard at runtime
    source = cast("PokemonCard", action.source)
    target = cast("PokemonCard", action.target)

    damage = _calculate_damage(source, target, action.attack.damage, state)
    player.reward.apply_damage_dealt_reward(damage)

    if target.hp > damage:
        target.hp -= damage
    else:
        yield from _handle_knockout(target, player, opponent, state)

    if auto_end_turn:
        next_turn(state)


def reduce_effect_action(
    action: EffectAction,
    state: "State",
) -> StepGenerator:
    """Reduce an effect action (e.g., damage counters from abilities).

    Handles damage application, knockout logic, and prize card selection.

    Args:
        action: The effect action to process.
        state: Current game state.

    Yields:
        (obs, reward, done, info) for any card selections needed.
    """
    trigger_attack_abilities(action, state)
    player = current_player(state)
    opponent = opponent_player(state)

    # action.target is typed as Card in action.py but is always PokemonCard at runtime
    target = cast("PokemonCard", action.target)

    damage = action.effect.dc * DAMAGE_COUNTER_MULTIPLIER
    player.reward.apply_damage_dealt_reward(damage)

    if target.hp > damage:
        target.hp -= damage
    else:
        yield from _handle_knockout(target, player, opponent, state)


def reduce_use_ability_action(action, state: "State") -> None:
    """Reduce an ability usage action.

    Args:
        action: The ability action to process.
        state: Current game state.

    Note:
        Currently not implemented.
    """
    raise NotImplementedError("Ability action reduction not yet implemented")


def reduce_use_stadium_action(action, state: "State") -> None:
    """Reduce a stadium usage action.

    Args:
        action: The stadium action to process.
        state: Current game state.

    Note:
        Currently not implemented.
    """
    raise NotImplementedError("Stadium action reduction not yet implemented")


def reduce_retreat_action(
    action: RetreatAction,
    state: "State",
) -> StepGenerator:
    """Reduce a retreat action.

    Handles:
    1. Choosing retreat target from bench
    2. Triggering retreat abilities
    3. Discarding retreat cost energy
    4. Switching Pokemon positions

    Args:
        action: The retreat action to process.
        state: Current game state.

    Yields:
        (obs, reward, done, info) for card selections needed.
    """
    player = current_player(state)
    current_active_pokemon = current_active(state)[0]

    tips = "You retreated your active Pokemon. You should choose 1 of your benched Pokemon and switch it to your active spot."
    actions = choose_card_actions(player.id, player.id, 1, 1, player.bench, tips=tips)
    target = yield from reduce_choose_card_actions(actions, state)
    target = target[0]

    trigger_retreat_abilities(action, state)

    retreat_cnt = len(current_active_pokemon.retreat)

    # Skip energy discard if retreat cost is 0
    if retreat_cnt > 0:
        energy_cards = [
            card for card in current_active_pokemon.attachment if card.superType == SuperType.ENERGY
        ]
        # Cast to EnergyCard list for retreat_combinations (we filtered by ENERGY superType)
        energy_cards_as_energy = cast(List["EnergyCard"], energy_cards)
        available_actions = [
            ChooseCardAction(
                player.id,
                player.id,
                cast(List["Card"], combo),  # EnergyCard is subclass of Card
                energy_cards,
            )
            for combo in retreat_combinations(energy_cards_as_energy, retreat_cnt)
        ]
        tips = "You retreated your active Pokemon. You should discard some energies attached to it."
        prompt = ChooseCardPrompt(0, len(energy_cards), energy_cards, tips=tips)
        actions = (available_actions, prompt)
        chosen_card = yield from reduce_choose_card_actions(actions, state)

        for card in chosen_card:
            for energy_provide in cast(Any, card).provides:
                current_active_pokemon.energy.remove(energy_provide)

        move_cards(
            chosen_card,
            (player.id, CardPosition.ACTIVE_ATTACHMENT),
            (player.id, CardPosition.DISCARD),
            state,
        )

    switch_pokemon(current_active_pokemon, target, player)


def reduce_play_pokemon_action(
    action: PlayPokemonAction,
    state: "State",
) -> None:
    """Reduce a play Pokemon action.

    Places a basic Pokemon from hand to active spot or bench.

    Args:
        action: The play Pokemon action to process.
        state: Current game state.

    Raises:
        CardPlayError: If the card cannot be played to the specified position.
    """
    if action.playerId == PlayerId.PLAYER1:
        player = state.player1
    else:
        player = state.player2

    card = cast("PokemonCard", action.source)

    try:
        if action.position == PokemonPosition.ACTIVE:
            player.hand.remove(card)
            player.active.append(card)
            card.position = PokemonPosition.ACTIVE
            card.cardPosition = CardPosition.ACTIVE
            card.index = 1
        elif action.position == PokemonPosition.BENCH:
            player.hand.remove(card)
            player.bench.append(card)
            card.position = PokemonPosition.BENCH
            card.cardPosition = CardPosition.BENCH
            card.index = len(player.bench)
        else:
            raise InvalidCardPositionError(
                f"Invalid position for playing Pokemon: {action.position}"
            )
    except ValueError as e:
        raise CardPlayError(f"Cannot play {card.name}: card not in hand") from e

    for idx, c in enumerate(player.hand):
        c.index = idx + 1


def reduce_evolve_pokemon_action(
    action: EvolvePokemonAction,
    state: "State",
) -> None:
    """Reduce an evolve Pokemon action.

    Evolves a Pokemon on the field, transferring energy and attachments.

    Args:
        action: The evolve action to process.
        state: Current game state.
    """
    player = current_player(state)
    evolved_card = cast("PokemonCard", action.source)
    evolving_card = cast("PokemonCard", action.target)
    player.reward.apply_pokemon_evolved_reward(1)

    evolved_card.energy = evolving_card.energy.copy()
    evolved_card.attachment = evolving_card.attachment.copy()
    evolved_card.position = evolving_card.position
    evolved_card.cardPosition = evolving_card.cardPosition
    evolved_card.index = evolving_card.index

    evolving_card.energy.clear()
    evolving_card.attachment.clear()

    evolved_card.evolved.append(evolving_card)

    if evolving_card.position == PokemonPosition.ACTIVE:
        player.active[evolving_card.index - 1] = evolved_card
    elif evolving_card.position == PokemonPosition.BENCH:
        player.bench[evolving_card.index - 1] = evolved_card

    player.hand.remove(evolved_card)
    for idx, c in enumerate(player.hand):
        c.index = idx + 1


def reduce_attach_energy_action(
    action: AttachEnergyAction,
    state: "State",
) -> None:
    """Reduce an attach energy action.

    Attaches an energy card from hand to a Pokemon in play.
    The target Pokemon must be set on action.target before calling.

    Args:
        action: The attach energy action to process (must have target set).
        state: Current game state.
    """
    from ptcg.core.card import EnergyCard

    player = current_player(state)
    player.energyPlayedTurn = True
    player.reward.apply_energy_attached_reward(1)

    target = cast("PokemonCard", action.target)
    energy_card = cast(EnergyCard, action.source)
    target.energy.extend(energy_card.provides)

    if target.cardPosition == CardPosition.ACTIVE:
        move_cards(
            action.source,
            (player.id, CardPosition.HAND),
            (player.id, CardPosition.ACTIVE_ATTACHMENT, target.index),
            state,
        )
    else:
        move_cards(
            action.source,
            (player.id, CardPosition.HAND),
            (player.id, CardPosition.BENCH_ATTACHMENT, target.index),
            state,
        )


def reduce_choose_card_actions(
    actions: Tuple[List[ChooseCardAction], ChooseCardPrompt],
    state: "State",
) -> Generator[Tuple["State", float, bool, dict], ChooseCardAction, List["Card"]]:
    """Reduce a card selection prompt.

    This generator pauses execution to let the player choose cards,
    then resumes with their selection.

    Args:
        actions: Tuple of (available actions, prompt info).
        state: Current game state.

    Yields:
        (obs, reward, done, info) for the selection prompt.

    Returns:
        List of chosen cards.

    Note:
        If player provides invalid action, a random valid one is chosen.
    """
    available_actions, prompt = actions

    if available_actions[0].playerId == PlayerId.PLAYER1:
        player = state.player1
    elif available_actions[0].playerId == PlayerId.PLAYER2:
        player = state.player2
    else:
        raise ValueError(f"Invalid player ID: {available_actions[0].playerId}")

    # Set state to indicate card selection is in progress
    state.is_choosing_card = True
    state.choose_card_list = prompt.candidates

    obs = state.get_obs()
    done = False
    reward = player.reward.calculate_step_reward()
    info = {
        "is_choosing_card": state.is_choosing_card,
        "raw_available_actions": available_actions,
        "prompt": prompt,
        "turn": state.turn,
        "full_state": state,
        "auto_executed": list(state.auto_events),
    }
    state.auto_events = []

    choose_card_action = yield (obs, reward, done, info)

    # Validate action - fall back to random if invalid
    if choose_card_action not in available_actions:
        logger.debug(f"{state.turn} invalid choose card action: {choose_card_action}")
        choose_card_action = random.choice(available_actions)

    chosen_card = choose_card_action.chosen
    state.actions_buffer.append(choose_card_action)

    # Reset selection state
    state.is_choosing_card = False

    return chosen_card


def reduce_choose_active_action() -> None:
    """Reduce action for choosing active Pokemon when spot is empty.

    This handles cases at game start or when active Pokemon is knocked out.

    Note:
        Currently not implemented.
    """
    raise NotImplementedError("Choose active action reduction not yet implemented")
