from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple

from ptcg.core.card import Card, StadiumCard
from ptcg.core.enums import CardPosition, PlayerId
from ptcg.core.player import Player

if TYPE_CHECKING:
    from ptcg.core.action import Action


@dataclass
class State:
    player1: Player
    player2: Player
    turn: Optional[PlayerId] = None
    timestep: int = 0
    turn_number: int = 0
    is_choosing_card: bool = False
    end_turn: bool = False
    stadium: List[StadiumCard] = field(default_factory=list)
    choose_card_list: List[Card] = field(default_factory=list)
    actions_buffer: List[Action] = field(default_factory=list)
    last_turn_opponent_actions: List[Action] = field(default_factory=list)
    turn_just_switched: bool = False
    auto_events: List[str] = field(default_factory=list)

    def get_area(self, area: Tuple[PlayerId, CardPosition, Optional[int]]) -> Sequence[Card]:
        if area[1] == CardPosition.STADIUM:
            return self.stadium

        if area[0] == self.player1.id:
            player = self.player1
        else:
            player = self.player2

        if area[1] == CardPosition.ACTIVE:
            return player.active
        elif area[1] == CardPosition.BENCH:
            return player.bench
        elif area[1] == CardPosition.HAND:
            return player.hand
        elif area[1] == CardPosition.LEFT:
            return player.left
        elif area[1] == CardPosition.DISCARD:
            return player.discard
        elif area[1] == CardPosition.LOSTZONE:
            return player.lostZone
        elif area[1] == CardPosition.PRIZE:
            return player.prize
        elif area[1] == CardPosition.ACTIVE_ATTACHMENT:
            return player.active[0].attachment
        elif area[1] == CardPosition.BENCH_ATTACHMENT:
            idx = area[2]
            if idx is None:
                from ptcg.core.exceptions import InvalidAreaError

                raise InvalidAreaError("Invalid area: bench attachment index is None")
            return player.bench[idx - 1].attachment
        else:
            from ptcg.core.exceptions import InvalidAreaError

            raise InvalidAreaError(f"Invalid area: {area}")

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        result["player1"] = self.player1.to_dict()
        result["player2"] = self.player2.to_dict()
        result["stadium"] = [self.stadium[0].to_dict()] if self.stadium else []
        result["turn"] = self.turn.name.lower() if self.turn else "none"
        result["timestep"] = self.timestep
        result["turn_number"] = self.turn_number

        return result

    def get_obs(self) -> State:
        return self

    def get_opponent_actions_buffer(self) -> List[Action]:
        opponent_actions: List[Action] = []
        for action in self.actions_buffer[::-1]:
            if action.playerId != self.turn:
                opponent_actions.append(action)
            else:
                break
        return list(reversed(opponent_actions))
