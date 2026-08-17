from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from copy import deepcopy
from math import comb
from typing import TYPE_CHECKING, Any, overload

from ptcg.core.enums import ActionType, CardPosition, PlayerId, PokemonPosition

if TYPE_CHECKING:
    from ptcg.core.ability import Ability
    from ptcg.core.attack import Attack
    from ptcg.core.card import Card
    from ptcg.core.player import Player


class Action(ABC):
    """
    params:
        playerId (PlayerId): who play this action
        source (card): which card this action is about (set by subclasses)
    """

    playerId: PlayerId
    actionType: ActionType

    def __init__(self, playerId: PlayerId, actionType: ActionType) -> None:
        self.playerId = playerId
        self.actionType = actionType

    def _player_str(self) -> str:
        if self.playerId == PlayerId.PLAYER1:
            return "Player1"
        elif self.playerId == PlayerId.PLAYER2:
            return "Player2"
        else:
            return "Player?"

    @abstractmethod
    def to_nl(self) -> str:
        pass

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        result["playerId"] = f"{self.playerId}"
        result["actionType"] = self.__class__.__name__

        if hasattr(self, "source") and hasattr(self.source, "name"):
            result["source"] = self.source.name

        result.update(self._extra_dict())
        return result

    def _extra_dict(self) -> dict[str, Any]:
        """Override in subclasses to add extra serialization fields."""
        return {}


class AttackAction(Action):
    attack: Attack
    attack_template: Attack
    target: Card

    def __init__(self, playerId: PlayerId, source: Card, attack: Attack, target: Card) -> None:
        super().__init__(playerId, ActionType.ATTACK_ACTION)
        self.source = source
        # Card attacks are immutable definitions. Effects and variable-damage
        # reducers modify this per-action copy without leaking into future turns.
        self.attack_template = attack
        self.attack = deepcopy(attack)
        self.target = target

    def to_nl(self) -> str:
        return f"{self._player_str()}'s [{self.source.name}] attacked [{self.target.name}] with [{self.attack.name}] for {self.attack.damage} damage"

    def _extra_dict(self) -> dict[str, Any]:
        return {
            "target": self.target.name,
            "attack": {"name": self.attack.name, "damage": self.attack.damage},
        }


class EffectAction(Action):
    effect: Any
    target: Card

    def __init__(self, playerId: PlayerId, source: Card, effect: Any, target: Card) -> None:
        super().__init__(playerId, ActionType.EFFECT_ACTION)
        self.source = source
        self.effect = effect
        self.target = target

    def to_nl(self) -> str:
        return (
            f"{self._player_str()} applied effect from [{self.source.name}] to [{self.target.name}]"
        )


class UseAbilityAction(Action):
    ability: Ability

    def __init__(self, playerId: PlayerId, source: Card, ability: Ability) -> None:
        super().__init__(playerId, ActionType.USE_ABILITY_ACTION)
        self.source = source
        self.ability = ability

    def to_nl(self) -> str:
        return f"{self._player_str()} used [{self.source.name}]'s ability [{self.ability.name}]"

    def _extra_dict(self) -> dict[str, Any]:
        return {"ability": self.ability.name}


class UseStadiumAction(Action):
    def __init__(self, playerId: PlayerId, source: Card) -> None:
        super().__init__(playerId, ActionType.USE_STADIUM_ACTION)
        self.source = source

    def to_nl(self) -> str:
        return f"{self._player_str()} used stadium effect [{self.source.name}]"


class RetreatAction(Action):
    active_pokemon: Card

    def __init__(self, playerId: PlayerId, source: Card | Player, active_pokemon: Card) -> None:
        super().__init__(playerId, ActionType.RETREAT_ACTION)
        self.source = source
        self.active_pokemon = active_pokemon

    def to_nl(self) -> str:
        return f"{self._player_str()} retreated [{self.active_pokemon.name}]"


class PlayPokemonAction(Action):
    """
    params:
        position (PokemonPosition): active or bench
    """

    position: PokemonPosition

    def __init__(self, playerId: PlayerId, source: Card, position: PokemonPosition) -> None:
        super().__init__(playerId, ActionType.PLAY_POKEMON_ACTION)
        self.source = source
        self.position = position

    def to_nl(self) -> str:
        position_str = {
            PokemonPosition.ACTIVE: "the Active Spot",
            PokemonPosition.BENCH: "the Bench",
        }.get(self.position, "Unknown")
        return f"{self._player_str()} played [{self.source.name}] to {position_str}"

    def _extra_dict(self) -> dict[str, Any]:
        return {"position": str(self.position)}


class EvolvePokemonAction(Action):
    """
    params:
        source (PokemonCard): evolved card
        target (PokemonCard): to be evolved card
    """

    target: Card

    def __init__(self, playerId: PlayerId, source: Card, target: Card) -> None:
        super().__init__(playerId, ActionType.EVOLVE_POKEMON_ACTION)
        self.source = source
        self.target = target

    def to_nl(self) -> str:
        position_str = {
            CardPosition.ACTIVE: "Active Spot",
            CardPosition.BENCH: "Bench",
        }.get(self.target.cardPosition, "Unknown")
        return f"{self._player_str()} evolved [{self.target.name}] into [{self.source.name}] in the {position_str}"


class AttachEnergyAction(Action):
    target: Card

    def __init__(self, playerId: PlayerId, source: Card, target: Card) -> None:
        super().__init__(playerId, ActionType.ATTACH_ENERGY_ACTION)
        self.source = source
        self.target = target

    def to_nl(self) -> str:
        return f"{self._player_str()} attached [{self.source.name}] to [{self.target.name}]"

    def _extra_dict(self) -> dict[str, Any]:
        return {"target": self.target.name if hasattr(self.target, "name") else str(self.target)}


class UseSupporterAction(Action):
    def __init__(self, playerId: PlayerId, source: Card) -> None:
        super().__init__(playerId, ActionType.USE_SUPPORTER_ACTION)
        self.source = source

    def to_nl(self) -> str:
        return f"{self._player_str()} played supporter [{self.source.name}]"


class UseItemAction(Action):
    def __init__(self, playerId: PlayerId, source: Card) -> None:
        super().__init__(playerId, ActionType.USE_ITEM_ACTION)
        self.source = source

    def to_nl(self) -> str:
        return f"{self._player_str()} played item [{self.source.name}]"


class UseToolAction(Action):
    target: Card

    def __init__(self, playerId: PlayerId, source: Card, target: Card) -> None:
        super().__init__(playerId, ActionType.USE_TOOL_ACTION)
        self.source = source
        self.target = target

    def to_nl(self) -> str:
        return f"{self._player_str()} attached [{self.source.name}] to [{self.target.name}]"

    def _extra_dict(self) -> dict[str, Any]:
        return {"target": self.target.name if hasattr(self.target, "name") else str(self.target)}


class PutStadiumAction(Action):
    def __init__(self, playerId: PlayerId, source: Card) -> None:
        super().__init__(playerId, ActionType.PUT_STADIUM_ACTION)
        self.source = source

    def to_nl(self) -> str:
        return f"{self._player_str()} played a new stadium [{self.source.name}]"


class DiscardStadiumAction(Action):
    def __init__(self, playerId: PlayerId, source: Card) -> None:
        super().__init__(playerId, ActionType.DISCARD_STADIUM_ACTION)
        self.source = source

    def to_nl(self) -> str:
        return f"{self._player_str()} discarded stadium [{self.source.name}]"


class PassTurn(Action):
    def __init__(self, playerId: PlayerId, source: Card | Player) -> None:
        super().__init__(playerId, ActionType.PASS_TURN)
        self.source = source

    def to_nl(self) -> str:
        return f"{self._player_str()} passed the turn"


class ChooseCardAction(Action):
    """
    Choose card(s) from a list of candidates.

    params:
        playerId (PlayerId): who plays this action
        targetId (PlayerId): who receives this action
        chosen (List[Card]): cards that were selected
        candidates (List[Card]): all available cards to choose from
        indexed (bool): if True, card positions matter; if False, only card names matter
        hidden (bool): if True, card names are masked in serialization
    """

    targetId: PlayerId
    chosen: list[Card]
    candidates: list[Card]
    indexed: bool
    hidden: bool

    def __init__(
        self,
        playerId: PlayerId,
        targetId: PlayerId,
        chosen: list[Card],
        candidates: Sequence[Card],
        indexed: bool = False,
        hidden: bool = False,
    ) -> None:
        super().__init__(playerId, ActionType.CHOOSE_CARD_ACTION)
        self.targetId = targetId
        self.chosen = chosen
        self.candidates = list(candidates)
        self.indexed = indexed
        self.hidden = hidden

    def to_nl(self) -> str:
        if self.hidden:
            plural = "cards" if len(self.chosen) > 1 else "card"
            return f"{self._player_str()} chose {len(self.chosen)} hidden {plural}"
        card_str = ", ".join(self._choice_card_str(card) for card in self.chosen)
        plural = "cards" if len(self.chosen) > 1 else "card"
        return f"{self._player_str()} chose {plural}: {card_str}"

    def _choice_card_str(self, card: Card) -> str:
        if self._needs_field_index(card):
            return f"[{card.name}] (index={card.index})"
        return f"[{card.name}]"

    def _needs_field_index(self, card: Card) -> bool:
        if getattr(card, "cardPosition", None) not in (CardPosition.ACTIVE, CardPosition.BENCH):
            return False
        same_name_field_candidates = [
            candidate
            for candidate in self.candidates
            if candidate.name == card.name
            and getattr(candidate, "cardPosition", None)
            in (CardPosition.ACTIVE, CardPosition.BENCH)
        ]
        return len(same_name_field_candidates) > 1

    def _extra_dict(self) -> dict[str, Any]:
        if self.hidden:
            return {
                "chosen": [f"Hidden Card #{i + 1}" for i in range(len(self.chosen))],
                "candidates": [f"Hidden Card #{i + 1}" for i in range(len(self.candidates))],
            }
        return {
            "chosen": [card.name for card in self.chosen],
            "candidates": [card.name for card in self.candidates],
        }

    def choose_card_indices(self) -> list[int]:
        card_indices: list[int] = []
        for card in self.chosen:
            card_indices.append(self.candidates.index(card))
        return card_indices

    def choose_field_indices(self) -> list[int]:
        card_indices: list[int] = []
        for card in self.chosen:
            if getattr(card, "cardPosition", None) in (CardPosition.ACTIVE, CardPosition.BENCH):
                card_indices.append(card.index)
        return card_indices


class ChooseCardActionSpace(Sequence[ChooseCardAction]):
    """Lazy sequence of all valid combinations for one card-choice prompt."""

    def __init__(
        self,
        playerId: PlayerId,
        targetId: PlayerId,
        min_cnt: int,
        max_cnt: int,
        candidates: Sequence[Card],
        *,
        indexed: bool = False,
        hidden: bool = False,
    ) -> None:
        if min_cnt < 0 or max_cnt < min_cnt:
            raise ValueError(f"Invalid choice bounds: min_cnt={min_cnt}, max_cnt={max_cnt}")
        self.playerId = playerId
        self.targetId = targetId
        self.min_cnt = min_cnt
        self.max_cnt = max_cnt
        self.candidates = list(candidates)
        self.indexed = indexed
        self.hidden = hidden
        self._selection_counts = tuple(range(min_cnt, min(max_cnt, len(self.candidates)) + 1))
        self._size = sum(comb(len(self.candidates), count) for count in self._selection_counts)

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[ChooseCardAction]:
        for count in self._selection_counts:
            for chosen in itertools.combinations(self.candidates, count):
                yield self._make_action(list(chosen))

    @overload
    def __getitem__(self, index: int) -> ChooseCardAction: ...

    @overload
    def __getitem__(self, index: slice) -> list[ChooseCardAction]: ...

    def __getitem__(self, index: int | slice) -> ChooseCardAction | list[ChooseCardAction]:
        if isinstance(index, slice):
            return [self[position] for position in range(*index.indices(len(self)))]

        if index < 0:
            index += len(self)
        if index < 0 or index >= len(self):
            raise IndexError("choice action index out of range")

        for count in self._selection_counts:
            bucket_size = comb(len(self.candidates), count)
            if index < bucket_size:
                chosen_indices = self._unrank_combination(count, index)
                return self._make_action([self.candidates[position] for position in chosen_indices])
            index -= bucket_size
        raise IndexError("choice action index out of range")

    def __contains__(self, value: object) -> bool:
        if not isinstance(value, ChooseCardAction):
            return False
        if (
            value.playerId != self.playerId
            or value.targetId != self.targetId
            or value.indexed != self.indexed
            or value.hidden != self.hidden
            or not self.min_cnt <= len(value.chosen) <= self.max_cnt
            or len(value.candidates) != len(self.candidates)
            or any(
                actual is not expected
                for actual, expected in zip(value.candidates, self.candidates)
            )
        ):
            return False

        candidate_positions = {id(card): index for index, card in enumerate(self.candidates)}
        try:
            chosen_positions = [candidate_positions[id(card)] for card in value.chosen]
        except KeyError:
            return False
        return len(set(chosen_positions)) == len(chosen_positions) and chosen_positions == sorted(
            chosen_positions
        )

    def _make_action(self, chosen: list[Card]) -> ChooseCardAction:
        return ChooseCardAction(
            self.playerId,
            self.targetId,
            chosen=chosen,
            candidates=self.candidates,
            indexed=self.indexed,
            hidden=self.hidden,
        )

    def _unrank_combination(self, count: int, rank: int) -> list[int]:
        """Return the indices of the lexicographically ranked combination."""
        result: list[int] = []
        start = 0
        total_candidates = len(self.candidates)
        for position in range(count):
            remaining = count - position - 1
            for candidate_index in range(start, total_candidates - remaining):
                suffix_count = comb(total_candidates - candidate_index - 1, remaining)
                if rank < suffix_count:
                    result.append(candidate_index)
                    start = candidate_index + 1
                    break
                rank -= suffix_count
        return result


class ChooseCardPrompt:
    min_cnt: int
    max_cnt: int
    candidates: list[Card]
    hidden: bool
    tips: str
    source: Card | None

    def __init__(
        self,
        min_cnt: int,
        max_cnt: int,
        candidates: Sequence[Card],
        hidden: bool = False,
        tips: str = "",
        source: Card | None = None,
    ) -> None:
        self.min_cnt = min_cnt
        self.max_cnt = max_cnt
        self.candidates = list(candidates)
        self.hidden = hidden
        self.tips = tips
        self.source = source


def choose_card_actions(
    playerId: PlayerId,
    targetId: PlayerId,
    min_cnt: int,
    max_cnt: int,
    candidates: Sequence[Card],
    indexed: bool = False,
    hidden: bool = False,
    tips: str = "",
    source: Card | None = None,
) -> tuple[ChooseCardActionSpace, ChooseCardPrompt]:
    """
    Generate all possible ChooseCardAction combinations.

    Args:
        playerId: Who plays this action
        targetId: Who receives this action
        min_cnt: Minimum number of cards to choose
        max_cnt: Maximum number of cards to choose
        candidates: List of cards to choose from
        indexed: If True, card positions matter; if False, only names matter
        hidden: Whether the cards are hidden from opponent
        tips: Hint text for the choice
        source: The card that triggered this choice (stored on prompt, not actions)

    Returns:
        Tuple of (lazy sequence of possible actions, prompt info)
    """
    prompt = ChooseCardPrompt(min_cnt, max_cnt, candidates, hidden, tips, source=source)

    available_actions = ChooseCardActionSpace(
        playerId,
        targetId,
        min_cnt,
        max_cnt,
        candidates,
        indexed=indexed,
        hidden=hidden,
    )

    return (available_actions, prompt)
