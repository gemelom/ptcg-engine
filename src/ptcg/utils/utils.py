from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional, Tuple, Union, cast

from ptcg.core.ability import ActiveAbility
from ptcg.core.card import Card, EnergyCard, PokemonCard
from ptcg.core.enums import (
    ActionType,
    CardPosition,
    CardType,
    Coin,
    PlayerId,
    PokemonPosition,
    SuperType,
)

if TYPE_CHECKING:
    from ptcg.core.action import Action
    from ptcg.core.player import Player
    from ptcg.core.state import State


def flip_coin(state: Optional["State"] = None) -> Coin:
    if random.randint(0, 1) == 0:
        result = Coin.HEAD
    else:
        result = Coin.TAIL
    if state is not None:
        side = "HEADS" if result == Coin.HEAD else "TAILS"
        state.auto_events.append(f"Coin flip: {side}.")
    return result


def shuffle_cards(cards: List[Card]) -> None:
    random.shuffle(cards)
    for idx, card in enumerate(cards):
        card.index = idx + 1


def move_cards(
    cards: Union[Card, List[Card], Tuple[Card, ...]],
    source_pos: Tuple[PlayerId, CardPosition],
    target_pos: Tuple[PlayerId, CardPosition],
    state: State,
) -> None:
    """
    move cards among hand/left/prize/discard
    cards are appended to the end of target list in this way
    """
    source = state.get_area(source_pos)  # type: ignore[arg-type]
    target = state.get_area(target_pos)  # type: ignore[arg-type]
    c_cards: List[Card] = []

    if isinstance(cards, list) or isinstance(cards, tuple):
        cards_list = cast(List[Card], cards)
        for card in cards_list:
            c_cards.append(card)
        for card in c_cards:
            source.remove(card)  # type: ignore[union-attr]
        for card in c_cards:
            card.cardPosition = target_pos[1]
            if isinstance(card, PokemonCard):
                if target_pos[1] == CardPosition.ACTIVE:
                    card.position = PokemonPosition.ACTIVE
                elif target_pos[1] == CardPosition.BENCH:
                    card.position = PokemonPosition.BENCH
        target.extend(c_cards)  # type: ignore[union-attr]
    else:
        # print("move_cards", cards)
        source.remove(cards)  # type: ignore[union-attr]
        cards.cardPosition = target_pos[1]
        if isinstance(cards, PokemonCard):
            if target_pos[1] == CardPosition.ACTIVE:
                cards.position = PokemonPosition.ACTIVE
            elif target_pos[1] == CardPosition.BENCH:
                cards.position = PokemonPosition.BENCH
        target.append(cards)  # type: ignore[union-attr]

    for idx, card in enumerate(source):
        card.index = idx + 1
    for idx, card in enumerate(target):
        card.index = idx + 1


def move_pokemon(player: Player, pokemon: Union[PokemonCard, List[PokemonCard]]) -> None:
    """
    move pokemon between bench and target
    """
    pokemon_card: PokemonCard = (
        cast(List[PokemonCard], pokemon)[0] if isinstance(pokemon, list) else pokemon
    )

    try:
        if pokemon_card.position == PokemonPosition.ACTIVE:
            player.active.remove(pokemon_card)
            player.bench.append(pokemon_card)
            pokemon_card.position = PokemonPosition.BENCH
            pokemon_card.cardPosition = CardPosition.BENCH
        elif pokemon_card.position == PokemonPosition.BENCH:
            player.bench.remove(pokemon_card)
            player.active.append(pokemon_card)
            pokemon_card.position = PokemonPosition.ACTIVE
            pokemon_card.cardPosition = CardPosition.ACTIVE

            for idx, card in enumerate(player.active):
                card.index = idx + 1
            for idx, card in enumerate(player.bench):
                card.index = idx + 1
    except Exception as exc:
        raise ValueError(
            f"Failed to move pokemon {pokemon_card} from position {pokemon_card.position}"
        ) from exc


def switch_pokemon(pokemon1: PokemonCard, pokemon2: PokemonCard, player: Player) -> None:
    """
    Switch pokemon between active and bench
    """
    assert pokemon1.cardPosition != pokemon2.cardPosition

    def swap_pos() -> None:
        tmp_pos, tmp_card_pos, tmp_idx = pokemon1.position, pokemon1.cardPosition, pokemon1.index
        pokemon1.position, pokemon1.cardPosition, pokemon1.index = (
            pokemon2.position,
            pokemon2.cardPosition,
            pokemon2.index,
        )
        pokemon2.position, pokemon2.cardPosition, pokemon2.index = tmp_pos, tmp_card_pos, tmp_idx

    try:
        if (
            pokemon1.cardPosition == CardPosition.ACTIVE
            and pokemon2.cardPosition == CardPosition.BENCH
        ):
            player.active[pokemon1.index - 1], player.bench[pokemon2.index - 1] = pokemon2, pokemon1
            swap_pos()
        else:
            player.active[pokemon2.index - 1], player.bench[pokemon1.index - 1] = pokemon1, pokemon2
            swap_pos()
    except Exception as exc:
        raise RuntimeError(
            "Failed to switch pokemon "
            f"{pokemon1.cardPosition}:{pokemon1.index} and "
            f"{pokemon2.cardPosition}:{pokemon2.index}"
        ) from exc


def discard_pokemon(player: Player, pokemon: Union[PokemonCard, List[PokemonCard]]) -> None:
    """
    discard pokemon and all its attachment to discard
    """
    pokemon_card: PokemonCard = (
        cast(List[PokemonCard], pokemon)[0] if isinstance(pokemon, list) else pokemon
    )

    try:
        if pokemon_card.position == PokemonPosition.ACTIVE:
            player.active.remove(pokemon_card)
        elif pokemon_card.position == PokemonPosition.BENCH:
            player.bench.remove(pokemon_card)
            for idx, card in enumerate(player.bench):
                card.index = idx + 1
    except Exception as exc:
        raise ValueError(f"Failed to discard pokemon {pokemon_card}") from exc

    for card in pokemon_card.attachment:
        item = type(card)()
        item.cardPosition = CardPosition.DISCARD
        player.discard.append(item)

    if hasattr(pokemon_card, "evolved"):
        for card in pokemon_card.evolved:
            item = type(card)()
            item.cardPosition = CardPosition.DISCARD
            player.discard.append(item)

    item = type(pokemon_card)()
    item.cardPosition = CardPosition.DISCARD
    player.discard.append(item)

    for idx, card in enumerate(player.discard):
        card.index = idx + 1


def discard_card(player: Player, card: Card) -> None:
    item = type(card)()
    item.cardPosition = CardPosition.DISCARD
    item.index = len(player.discard) + 1
    player.discard.append(item)


def check_energy(cost: List[CardType], energy: List[CardType]) -> bool:
    """
    check energy for attack or retreat
    """
    cost.sort(key=lambda card: card.value, reverse=True)
    energy.sort(key=lambda card: card.value, reverse=True)

    i, j = 0, 0
    while i < len(cost):
        if j == len(energy):
            break
        if energy[j] == cost[i] or cost[i] == CardType.COLORLESS:
            i += 1
        j += 1

    if i == len(cost):
        return True
    else:
        return False


def check_evolve(evolved_card: PokemonCard, state: State) -> List[PokemonCard]:
    can_evolve: List[PokemonCard] = []
    for pokemon in current_all_pokemon(state):
        if pokemon.name == evolved_card.evolveFrom[0] and not pokemon.firstTurnPlayed:
            can_evolve.append(pokemon)

    return can_evolve


def judge_termination(state: State) -> Tuple[bool, Optional[PlayerId]]:
    """
    Judge whether the game ends

    Returns:
        terminated (bool): true if game terminated
        winner (PlayerId): winner playerId
    """
    terminated = False
    winner: Optional[PlayerId] = None
    player1, player2 = state.player1, state.player2
    if (
        len(player1.prize) == 0
        or len(player2.active) + len(player2.bench) == 0
        or len(player2.left) == 0
    ):
        terminated = True
        winner = player1.id
    elif (
        len(player2.prize) == 0
        or len(player1.active) + len(player1.bench) == 0
        or len(player1.left) == 0
    ):
        terminated = True
        winner = player2.id
    return terminated, winner


def next_turn(state: State) -> None:
    state.turn_number += 1
    player = current_player(state)

    # Extract current player's actions from this turn before switching.
    # These will become "opponent's last turn actions" for the next player.
    # Reactive ChooseCardActions from the opponent (e.g. bench replacement after KO)
    # may appear at the tail of actions_buffer after the current player's last action.
    # We skip those trailing opponent ChooseCardActions before collecting.
    current_turn_actions: List[Action] = []
    found_current_player = False
    for action in reversed(state.actions_buffer):
        if action.playerId == player.id:
            found_current_player = True
            current_turn_actions.append(action)
        elif not found_current_player and action.actionType == ActionType.CHOOSE_CARD_ACTION:
            # Skip opponent's reactive card selections at the tail (e.g. bench replacement)
            continue
        else:
            break
    state.last_turn_opponent_actions = list(reversed(current_turn_actions))
    state.turn_just_switched = True

    # Reset statistics at end of turn
    player.reset_turn_stats()

    # reset all pokemons' states
    for pokemon in current_all_pokemon(state):
        # Call reset_turn_stats method if it exists
        if hasattr(pokemon, "reset_turn_stats") and callable(getattr(pokemon, "reset_turn_stats")):
            pokemon.reset_turn_stats()  # type: ignore[union-attr]

        # reset active ability usability
        if hasattr(pokemon, "abilityUsed") and isinstance(pokemon.ability[0], ActiveAbility):
            pokemon.abilityUsed = False  # type: ignore[union-attr]
        # reset first turn played state
        if pokemon.firstTurnPlayed:
            pokemon.firstTurnPlayed = False
        # reset attack restriction for cards like Miraidon ex
        if hasattr(pokemon, "useAttackLastTurn"):
            pokemon.useAttackLastTurn = False  # type: ignore[union-attr]

    # reset player states
    for key in player.onceUsedTurn:
        player.onceUsedTurn[key] = False
    if player.firstTurn:
        player.firstTurn = False

    # pokemon dead last turn
    player.hasPokemonDead = False

    # change turn and draw one card
    done, _ = judge_termination(state)
    if done:  # can't draw card if game ends
        return

    if state.turn == state.player1.id:
        state.turn = state.player2.id
        new_player_name = "PLAYER2"
        move_cards(
            state.player2.left[0],
            (state.player2.id, CardPosition.LEFT),
            (state.player2.id, CardPosition.HAND),
            state,
        )
    else:
        state.turn = state.player1.id
        new_player_name = "PLAYER1"
        move_cards(
            state.player1.left[0],
            (state.player1.id, CardPosition.LEFT),
            (state.player1.id, CardPosition.HAND),
            state,
        )
    state.auto_events.append(f"Turn switched to {new_player_name}. 1 card drawn from deck to hand.")
    state.end_turn = True


def auto_end_turn(state: State) -> None:
    """
    automatically end turn after attack (if reduce_attack_action is not called) or ability
    """
    next_turn(state)


def opponent_active(state: State) -> List[PokemonCard]:
    """
    get opponent's active pokemon
    """
    if state.turn == state.player1.id:
        return state.player2.active
    else:
        return state.player1.active


def opponent_bench(state: State) -> List[PokemonCard]:
    """
    get opponent's bench pokemon
    """
    if state.turn == state.player1.id:
        return state.player2.bench
    else:
        return state.player1.bench


def opponent_all_pokemon(state: State) -> List[PokemonCard]:
    """
    get opponent's active pokemon + bench pokemon
    """
    if state.turn == state.player1.id:
        return state.player2.active + state.player2.bench
    else:
        return state.player1.active + state.player1.bench


def is_active_ability_suppressed(player: Player, state: State) -> bool:
    """Check if a player's active Pokémon's abilities are suppressed.

    Returns True if the opponent has a Pokémon in the Active Spot whose
    ability has suppresses_opponent_active_abilities set to True
    (e.g., Flutter Mane's Midnight Fluttering).
    """
    opponent = state.player1 if player == state.player2 else state.player2
    for pokemon in opponent.active:
        if hasattr(pokemon, "ability") and pokemon.ability:
            for ab in pokemon.ability:
                if getattr(ab, "suppresses_opponent_active_abilities", False):
                    return True
    return False


def current_active(state: State) -> List[PokemonCard]:
    """
    get my active pokemon
    """
    if state.turn == state.player1.id:
        return state.player1.active
    else:
        return state.player2.active


def current_bench(state: State) -> List[PokemonCard]:
    """
    get my bench pokemon
    """
    if state.turn == state.player1.id:
        return state.player1.bench
    else:
        return state.player2.bench


def current_all_pokemon(state: State) -> List[PokemonCard]:
    """
    get my active pokemon + bench pokemon
    """
    if state.turn == state.player1.id:
        return state.player1.active + state.player1.bench
    else:
        return state.player2.active + state.player2.bench


def current_player(state: State) -> Player:
    """
    get whose turn now
    """
    if state.turn == PlayerId.PLAYER1:
        return state.player1
    else:
        return state.player2


def opponent_player(state: State) -> Player:
    """
    get who play againt now
    """
    if state.turn == PlayerId.PLAYER1:
        return state.player2
    else:
        return state.player1


def can_attach_energy(state: State) -> bool:
    return not current_player(state).energyPlayedTurn


def can_attach_tool(pokemon: PokemonCard) -> bool:
    if hasattr(pokemon, "attachment") and all(
        card.superType != SuperType.TRAINER for card in pokemon.attachment
    ):
        return True
    else:
        return False


def retreat_combinations(energy: List[EnergyCard], retreat_cnt: int) -> List[List[EnergyCard]]:
    """
    get discard energy combinations for retreat
    """

    def check_combo(combo: List[EnergyCard]) -> bool:
        all_provides = 0
        for card in combo:
            all_provides += len(card.provides)
        if all_provides < retreat_cnt:
            return False
        for card in combo:
            if all_provides - len(card.provides) >= retreat_cnt:
                return False
        return True

    all_combinations: List[List[EnergyCard]] = [[]]
    for card in energy:
        all_combinations += [cur + [card] for cur in all_combinations]

    result: List[List[EnergyCard]] = []
    for combination in all_combinations:
        if check_combo(combination):
            result.append(combination)

    return result


def get_name(cards: List[Card]) -> List[str]:
    """
    get card name in a list, especially for print_log()
    """
    name_list: List[str] = []
    for card in cards:
        if hasattr(card, "name"):
            name_list.append(card.name)
    return name_list


# game termination eception
class GameTermination(Exception):
    pass
