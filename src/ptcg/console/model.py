"""Detached models shared by the interactive session and terminal adapters."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PlayConfig:
    deck: str | None = None
    opponent_deck: str | None = None
    opponent_policy: str = "random"
    seed: int = 0
    max_steps: int = 1000
    record: bool = False
    verbose: bool = False


@dataclass(frozen=True)
class CardView:
    reference: str
    name: str
    set_name: str
    number: str
    current_hp: str | None = None
    maximum_hp: str | None = None
    energy: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    details: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class PlayerView:
    player_id: str
    hand_count: int
    deck_count: int
    prize_count: int
    discard_count: int
    active: tuple[CardView, ...]
    bench: tuple[CardView, ...]
    hand: tuple[CardView, ...] = ()


@dataclass(frozen=True)
class ActionView:
    number: int
    group: str
    description: str
    card: CardView | None = None


@dataclass(frozen=True)
class ChoicePromptView:
    min_count: int
    max_count: int
    allowed_counts: tuple[int, ...]
    tips: str
    candidates: tuple[CardView, ...]


@dataclass(frozen=True)
class DecisionFrame:
    seed: int
    human_deck: str
    opponent_deck: str
    opponent_policy: str
    timestep: int
    turn_number: int
    turn: str | None
    human: PlayerView
    opponent: PlayerView
    stadium: tuple[CardView, ...]
    events: tuple[str, ...]
    actions: tuple[ActionView, ...]
    prompt: ChoicePromptView | None = None


@dataclass(frozen=True)
class SelectAction:
    index: int


@dataclass(frozen=True)
class SelectCandidates:
    indices: tuple[int, ...]


@dataclass(frozen=True)
class QuitGame:
    pass


HumanIntent = SelectAction | SelectCandidates | QuitGame


@dataclass(frozen=True)
class SessionResult:
    status: str
    steps: int
    reward: float
    winner: str | None = None
    reason: str | None = None
    events: tuple[str, ...] = ()

    @property
    def exit_code(self) -> int:
        if self.status == "finished":
            return 0
        if self.reason == "interrupt":
            return 130
        if self.status == "error":
            return 2
        return 1


class Terminal(Protocol):
    """Small seam implemented by RichTerminal and scripted test adapters."""

    def choose(self, frame: DecisionFrame) -> HumanIntent: ...

    def show_error(self, message: str) -> None: ...

    def show_result(self, result: SessionResult) -> None: ...
