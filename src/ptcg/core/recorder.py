"""Game recorder for replay and analysis.

This module provides the GameRecorder class for recording complete game
histories in JSONL format for replay and analysis purposes.

JSONL Format:
    Each line is a complete JSON object representing a game event:
    - {"type": "game_start", "first_player": "...", "state": {...}}
    - {"type": "action", "data": {...}}
    - {"type": "state", "data": {...}}
    - {"type": "termination", "winner": "..."}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ptcg.core.action import Action
    from ptcg.core.enums import PlayerId
    from ptcg.core.state import State


class EventType(Enum):
    """Types of game events that can be recorded."""

    GAME_START = "game_start"
    ACTION = "action"
    STATE = "state"
    CHOOSE_CARD_PROMPT = "choose_card_prompt"
    TERMINATION = "termination"


@dataclass
class GameEvent:
    """A single game event."""

    event_type: EventType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
        }


class GameRecorder:
    """Records game history for replay and analysis.

    This class handles game state/action recording, NOT debug logging.
    For debug logging, use loguru directly.

    Usage:
        recorder = GameRecorder(seed=42)
        recorder.record_game_start(first_player="player1", state=state)
        recorder.record_action(action)
        recorder.record_state(state)
        recorder.record_termination(winner="player1")
        recorder.save()  # Writes to ./battle_log/seed_42.jsonl

    To load and replay:
        history = GameRecorder.load("./battle_log/seed_42.jsonl")
        for event in history:
            print(event["type"], event["data"])
    """

    def __init__(
        self,
        seed: int,
        output_dir: str = "./battle_log",
        auto_save: bool = True,
    ):
        """Initialize the game recorder.

        Args:
            seed: Game seed for filename.
            output_dir: Directory to save recordings.
            auto_save: If True, save on record_termination().
        """
        self.seed = seed
        self.output_dir = output_dir
        self.auto_save = auto_save
        self.events: List[GameEvent] = []
        self._file_path: Optional[str] = None

    @property
    def file_path(self) -> str:
        """Get the output file path."""
        if self._file_path is None:
            self._file_path = str(Path(self.output_dir) / f"seed_{self.seed}.jsonl")
        return self._file_path

    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        Path(self.output_dir).mkdir(exist_ok=True)

    def record_game_start(self, first_player: str, state: State) -> None:
        """Record game start event.

        Args:
            first_player: Player who goes first.
            state: Initial game state.
        """
        event = GameEvent(
            event_type=EventType.GAME_START,
            data={
                "first_player": first_player,
                "state": state.to_dict(),
            },
        )
        self.events.append(event)

    def record_action(self, action: Action) -> None:
        """Record an action event.

        Args:
            action: The action to record.
        """
        event = GameEvent(
            event_type=EventType.ACTION,
            data=action.to_dict(),
        )
        self.events.append(event)

    def record_state(self, state: State) -> None:
        """Record a state snapshot.

        Args:
            state: Current game state.
        """
        event = GameEvent(
            event_type=EventType.STATE,
            data=state.to_dict(),
        )
        self.events.append(event)

    def record_choose_card_prompt(
        self,
        min_cnt: int,
        max_cnt: int,
        candidates: List[str],
        tips: str = "",
    ) -> None:
        """Record a card selection prompt.

        Args:
            min_cnt: Minimum cards to select.
            max_cnt: Maximum cards to select.
            candidates: List of candidate card names.
            tips: Hint text for the choice.
        """
        event = GameEvent(
            event_type=EventType.CHOOSE_CARD_PROMPT,
            data={
                "min_cnt": min_cnt,
                "max_cnt": max_cnt,
                "candidates": candidates,
                "tips": tips,
            },
        )
        self.events.append(event)

    def record_termination(self, winner: Optional[PlayerId]) -> None:
        """Record game termination event.

        Args:
            winner: Winner player ID, or None for draw.
        """
        event = GameEvent(
            event_type=EventType.TERMINATION,
            data={
                "winner": winner.name if winner else None,
            },
        )
        self.events.append(event)

        if self.auto_save:
            self.save()

    def save(self) -> str:
        """Save all recorded events to JSONL file.

        Returns:
            Path to the saved file.
        """
        self._ensure_output_dir()

        with open(self.file_path, "w", encoding="utf-8") as f:
            for event in self.events:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

        return self.file_path

    def clear(self) -> None:
        """Clear all recorded events."""
        self.events.clear()

    @staticmethod
    def load(file_path: str) -> List[Dict[str, Any]]:
        """Load game history from JSONL file.

        Args:
            file_path: Path to the recording file.

        Returns:
            List of event dictionaries.
        """
        events = []
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the recorded game.

        Returns:
            Summary with event counts and metadata.
        """
        action_counts: Dict[str, int] = {}
        for event in self.events:
            if event.event_type == EventType.ACTION:
                action_type = event.data.get("actionType", "Unknown")
                action_counts[action_type] = action_counts.get(action_type, 0) + 1

        return {
            "seed": self.seed,
            "total_events": len(self.events),
            "action_counts": action_counts,
            "file_path": self.file_path,
        }
