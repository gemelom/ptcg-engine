"""Rich terminal adapter for interactive matches."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ptcg.console.model import (
    ActionView,
    CardView,
    DecisionFrame,
    HumanIntent,
    PlayerView,
    QuitGame,
    SelectAction,
    SelectCandidates,
    SessionResult,
)

# Console provides capability detection, width-aware rendering, input, and
# StringIO-backed testing: https://rich.readthedocs.io/en/latest/console.html
# Table provides responsive, border-optional terminal layouts:
# https://rich.readthedocs.io/en/latest/tables.html#table-options
_GROUP_ORDER = {
    name: index
    for index, name in enumerate(("Play", "Attach", "Ability", "Field", "Attack", "Turn", "Other"))
}


class RichTerminal:
    """Render decision frames and translate command-loop input into intents."""

    def __init__(
        self,
        console: Console | None = None,
        *,
        read_line: Callable[[str], str] | None = None,
    ) -> None:
        self.console = console or Console()
        self._read_line = read_line

    def choose(self, frame: DecisionFrame) -> HumanIntent:
        self._render_frame(frame)
        while True:
            raw = self._input("[bold cyan]ptcg>[/] ").strip()
            lowered = raw.lower()

            if lowered in {"quit", "exit", "q"}:
                if self._confirm_quit():
                    return QuitGame()
                continue
            if lowered == "board":
                self._render_board(frame)
                continue
            if lowered == "hand":
                self._render_hand(frame.human.hand)
                continue
            if lowered == "help":
                self._render_help(frame.prompt is not None)
                continue
            if lowered.startswith("inspect"):
                self._inspect(frame, raw.split()[1:])
                continue

            if frame.prompt is not None:
                intent = self._parse_candidate_selection(raw, frame)
                if intent is not None:
                    return intent
                continue

            if raw.isdigit():
                number = int(raw)
                if 1 <= number <= len(frame.actions):
                    return SelectAction(number - 1)
                self.show_error(f"Action number must be between 1 and {len(frame.actions)}.")
                continue

            self.show_error("Enter an action number or type help.")

    def show_error(self, message: str) -> None:
        self.console.print(Text(message, style="bold red"))

    def show_result(self, result: SessionResult) -> None:
        if result.events:
            self.console.print()
            self.console.print(Text("Final events", style="bold"))
            for event in result.events:
                self.console.print(Text(f"  {event}"))
        self.console.rule(style="dim")
        if result.status == "finished":
            winner = result.winner or "draw"
            self.console.print(
                f"[bold green]Game finished[/] in {result.steps} steps. "
                f"Winner: {winner}. Reward: {result.reward:g}."
            )
        else:
            self.console.print(
                f"[bold yellow]Game {result.status}[/] after {result.steps} steps "
                f"({result.reason})."
            )

    def _render_frame(self, frame: DecisionFrame) -> None:
        self.console.print()
        self.console.print(
            f"[bold cyan]PTCG ENGINE[/]  Turn {frame.turn_number} · Decision {frame.timestep} "
            f"· Seed {frame.seed} · Opponent: {frame.opponent_policy}"
        )
        self.console.print(
            Text(
                f"Deck: {frame.human_deck} · Opponent deck: {frame.opponent_deck}",
                style="dim",
            )
        )
        self.console.rule(style="dim")
        if frame.events:
            self.console.print(Text("Since your last decision", style="dim"))
            for event in frame.events:
                self.console.print(Text(f"  {event}"))
            self.console.print()

        self._render_board(frame)
        self.console.print()
        self._render_hand(frame.human.hand)
        self.console.print()
        if frame.prompt is not None:
            self._render_prompt(frame)
        else:
            self._render_actions(frame.actions)
        self._render_help(frame.prompt is not None, compact=True)

    def _render_board(self, frame: DecisionFrame) -> None:
        self._render_player("OPPONENT", frame.opponent, "red")
        stadium_names = ", ".join(card.name for card in frame.stadium)
        self.console.print(
            Panel(
                Text(stadium_names),
                title="STADIUM",
                title_align="left",
                border_style="dim",
                box=box.ROUNDED,
                padding=(0, 1),
            )
        )
        self._render_player("YOU", frame.human, "green")

    def _render_player(self, label: str, player: PlayerView, style: str) -> None:
        summary = Text(
            f"Prize {player.prize_count} · Hand {player.hand_count} · "
            f"Deck {player.deck_count} · Discard {player.discard_count}",
            style="dim",
        )
        table = Table(
            box=None,
            show_header=True,
            header_style="dim",
            padding=(0, 1),
            collapse_padding=True,
            expand=True,
        )
        table.add_column("Slot", style="dim", no_wrap=True)
        table.add_column("Card", ratio=2)
        table.add_column("HP", no_wrap=True)
        table.add_column("Energy", ratio=1)
        table.add_column("Tool", ratio=1)
        cards = (*player.active, *player.bench)
        for card in cards:
            slot = "Active" if card.reference.startswith("A") else f"Bench {card.reference[1:]}"
            hp = self._hp(card)
            table.add_row(
                slot,
                Text(card.name),
                hp,
                ", ".join(card.energy),
                ", ".join(card.tools),
            )
        contents = Group(summary, table) if cards else summary
        panel = Panel(
            contents,
            title=Text(f"{label} · {player.player_id.upper()}", style=f"bold {style}"),
            title_align="left",
            border_style=style,
            box=box.ROUNDED,
            padding=(0, 1),
        )
        self.console.print(panel)

    def _render_hand(self, hand: Sequence[CardView]) -> None:
        self.console.print(Text("YOUR HAND", style="bold"))
        if not hand:
            self.console.print(Text("  Empty", style="dim"))
            return
        table = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        table.add_column("Ref", style="cyan", no_wrap=True)
        table.add_column("Card", ratio=2)
        table.add_column("Set", style="dim", no_wrap=True)
        for card in hand:
            table.add_row(card.reference, Text(card.name), f"{card.set_name} {card.number}")
        self.console.print(table)

    def _render_actions(self, actions: Sequence[ActionView]) -> None:
        self.console.print(Text("LEGAL ACTIONS", style="bold"))
        table = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        table.add_column("Group", style="dim", no_wrap=True)
        table.add_column("No.", style="cyan", justify="right", no_wrap=True)
        table.add_column("Action", ratio=4)
        previous_group = None
        for action in sorted(actions, key=lambda item: _GROUP_ORDER.get(item.group, 999)):
            group = action.group if action.group != previous_group else ""
            table.add_row(group, str(action.number), Text(action.description))
            previous_group = action.group
        self.console.print(table)

    def _render_prompt(self, frame: DecisionFrame) -> None:
        prompt = frame.prompt
        if prompt is None:
            return
        heading = prompt.tips or f"Choose {prompt.min_count}–{prompt.max_count} cards."
        self.console.print(Text(heading, style="bold"))
        table = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        table.add_column("Ref", style="cyan", no_wrap=True)
        table.add_column("Candidate", ratio=3)
        table.add_column("Set", style="dim", no_wrap=True)
        for card in prompt.candidates:
            card_set = f"{card.set_name} {card.number}".strip()
            table.add_row(card.reference, Text(card.name), card_set)
        self.console.print(table)
        count_text = self._choice_count_text(prompt.allowed_counts)
        self.console.print(
            Text(
                f"Select {count_text} candidate numbers separated by spaces or commas.",
                style="dim",
            )
        )

    def _render_help(self, choosing_cards: bool, *, compact: bool = False) -> None:
        if compact:
            command = "<candidate numbers>" if choosing_cards else "<action number>"
            self.console.print(
                Text(
                    f"Commands: {command} · board · hand · inspect <area> <number> · help · quit",
                    style="dim",
                )
            )
            return
        self.console.print(Text("Commands", style="bold"))
        self.console.print("  <number>                  Execute a legal action")
        self.console.print("  <n1> <n2>                Select card candidates when prompted")
        self.console.print("  board | hand             Reprint public board or your hand")
        self.console.print("  inspect action <n>       Inspect an action's source card")
        self.console.print("  inspect hand <n>         Inspect a card in your hand")
        self.console.print("  inspect active [n]       Inspect your Active Pokemon")
        self.console.print("  inspect bench <n>        Inspect your Benched Pokemon")
        self.console.print("  inspect opponent <area>  Inspect an opponent field card")
        self.console.print("  inspect stadium [n]      Inspect a Stadium")
        self.console.print("  quit                     Leave the current game")

    def _parse_candidate_selection(
        self,
        raw: str,
        frame: DecisionFrame,
    ) -> SelectCandidates | None:
        prompt = frame.prompt
        if prompt is None:
            return None
        if (not raw and 0 in prompt.allowed_counts) or raw.lower() == "none":
            indices: tuple[int, ...] = ()
        else:
            parts = raw.replace(",", " ").split()
            try:
                numbers = [int(part.removeprefix("C").removeprefix("c")) for part in parts]
            except ValueError:
                self.show_error("Enter candidate numbers separated by spaces or commas.")
                return None
            indices = tuple(number - 1 for number in numbers)

        if len(set(indices)) != len(indices):
            self.show_error("Candidate numbers must be unique.")
            return None
        if len(indices) not in prompt.allowed_counts:
            allowed = self._choice_count_text(prompt.allowed_counts)
            self.show_error(f"Choose {allowed} cards.")
            return None
        if any(index < 0 or index >= len(prompt.candidates) for index in indices):
            self.show_error(f"Candidate numbers must be between 1 and {len(prompt.candidates)}.")
            return None
        return SelectCandidates(tuple(sorted(indices)))

    @staticmethod
    def _choice_count_text(counts: Sequence[int]) -> str:
        if len(counts) == 1:
            return str(counts[0])
        if tuple(counts) == tuple(range(counts[0], counts[-1] + 1)):
            return f"{counts[0]}–{counts[-1]}"
        return ", ".join(str(count) for count in counts[:-1]) + f" or {counts[-1]}"

    def _inspect(self, frame: DecisionFrame, parts: Sequence[str]) -> None:
        card = self._resolve_card(frame, [part.lower() for part in parts])
        if card is None:
            self.show_error("Card not found. Type help for inspect syntax.")
            return
        self._render_card_details(card)

    def _resolve_card(self, frame: DecisionFrame, parts: Sequence[str]) -> CardView | None:
        if not parts:
            return None
        area = parts[0]
        if area == "action" and len(parts) == 2 and parts[1].isdigit():
            action_number = int(parts[1])
            action = next((item for item in frame.actions if item.number == action_number), None)
            return action.card if action else None
        if area == "hand" and len(parts) == 2:
            return self._by_number(frame.human.hand, parts[1])
        if area == "active":
            return self._by_number(frame.human.active, parts[1] if len(parts) > 1 else "1")
        if area == "bench" and len(parts) == 2:
            return self._by_number(frame.human.bench, parts[1])
        if area == "stadium":
            return self._by_number(frame.stadium, parts[1] if len(parts) > 1 else "1")
        if area == "opponent" and len(parts) >= 2:
            opponent_area = parts[1]
            opponent_number = parts[2] if len(parts) > 2 else "1"
            if opponent_area == "active":
                return self._by_number(frame.opponent.active, opponent_number)
            if opponent_area == "bench":
                return self._by_number(frame.opponent.bench, opponent_number)
        return None

    @staticmethod
    def _by_number(cards: Sequence[CardView], value: str) -> CardView | None:
        value = value.removeprefix("h").removeprefix("a").removeprefix("b")
        if not value.isdigit():
            return None
        index = int(value) - 1
        return cards[index] if 0 <= index < len(cards) else None

    def _render_card_details(self, card: CardView) -> None:
        self.console.print()
        self.console.print(Text(f"{card.name} · {card.set_name} {card.number}", style="bold cyan"))
        if not card.details:
            self.console.print(Text("No card details are available.", style="dim"))
            return
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        table.add_column("Field", style="dim", no_wrap=True)
        table.add_column("Value", ratio=4)
        for key, value in card.details.items():
            if key in {"id", "name", "set_name", "number"}:
                continue
            table.add_row(key, Text(self._format_detail(value)))
        self.console.print(table)

    @classmethod
    def _format_detail(cls, value: Any) -> str:
        if isinstance(value, Mapping):
            return ", ".join(f"{key}: {cls._format_detail(item)}" for key, item in value.items())
        if isinstance(value, tuple):
            return "; ".join(cls._format_detail(item) for item in value) or "—"
        return str(value)

    def _confirm_quit(self) -> bool:
        answer = self._input("[yellow]Quit this game? (y/N)[/] ").strip().lower()
        return answer in {"y", "yes"}

    def _input(self, prompt: str) -> str:
        if self._read_line is None:
            # Source: https://rich.readthedocs.io/en/latest/console.html#input
            return self.console.input(prompt)
        self.console.print(prompt, end="")
        return self._read_line(prompt)

    @staticmethod
    def _hp(card: CardView) -> str:
        if card.current_hp is None:
            return ""
        if card.maximum_hp and card.maximum_hp != card.current_hp:
            return f"{card.current_hp}/{card.maximum_hp}"
        return card.current_hp
