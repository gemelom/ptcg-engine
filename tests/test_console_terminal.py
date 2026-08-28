from __future__ import annotations

from io import StringIO
from types import MappingProxyType

from rich.console import Console

from ptcg.console.model import (
    ActionView,
    CardView,
    ChoicePromptView,
    DecisionFrame,
    PlayerView,
    QuitGame,
    SelectAction,
    SelectCandidates,
    SessionResult,
)
from ptcg.console.terminal import RichTerminal


def _card(reference: str, name: str) -> CardView:
    return CardView(
        reference=reference,
        name=name,
        set_name="PAF",
        number="007",
        current_hp="70",
        maximum_hp="70",
        details=MappingProxyType(
            {
                "name": name,
                "superType": "POKEMON",
                "hp": 70,
                "attacks": (MappingProxyType({"name": "Scratch", "damage": 10}),),
            }
        ),
    )


def _frame(*, prompt: ChoicePromptView | None = None) -> DecisionFrame:
    human_card = _card("A1", "Charmander")
    hand_card = _card("H1", "Charmander")
    opponent_card = _card("A1", "Miraidon ex")
    return DecisionFrame(
        seed=42,
        human_deck="charizard_ex",
        opponent_deck="miraidon_ex",
        opponent_policy="random",
        timestep=23,
        turn_number=4,
        turn="player1",
        human=PlayerView(
            player_id="player1",
            hand_count=1,
            deck_count=45,
            prize_count=6,
            discard_count=1,
            active=(human_card,),
            bench=(),
            hand=(hand_card,),
        ),
        opponent=PlayerView(
            player_id="player2",
            hand_count=5,
            deck_count=44,
            prize_count=6,
            discard_count=2,
            active=(opponent_card,),
            bench=(),
        ),
        stadium=(),
        events=("Player2 passed the turn",),
        actions=(ActionView(1, "Turn", "Player1 passed the turn", human_card),),
        prompt=prompt,
    )


def _terminal(inputs: list[str], *, width: int = 80):
    # Rich recommends a StringIO-backed Console for output tests:
    # https://rich.readthedocs.io/en/latest/console.html#capturing-output
    output = StringIO()
    iterator = iter(inputs)
    console = Console(file=output, color_system=None, width=width)
    terminal = RichTerminal(console, read_line=lambda _prompt: next(iterator))
    return terminal, output


def test_rich_terminal_renders_inspection_then_returns_numbered_action():
    terminal, output = _terminal(["inspect hand 1", "1"])

    intent = terminal.choose(_frame())

    assert intent == SelectAction(0)
    rendered = output.getvalue()
    assert "PTCG ENGINE" in rendered
    assert "OPPONENT · PLAYER2" in rendered
    assert "YOUR HAND" in rendered
    assert "Charmander · PAF 007" in rendered
    assert "LEGAL ACTIONS" in rendered
    assert "\x1b[" not in rendered


def test_rich_terminal_parses_candidate_numbers_with_commas_and_prefixes():
    prompt = ChoicePromptView(
        min_count=1,
        max_count=2,
        allowed_counts=(1, 2),
        tips="Choose cards",
        candidates=(_card("C1", "First"), _card("C2", "Second"), _card("C3", "Third")),
    )
    terminal, _output = _terminal(["C3, c1"])

    intent = terminal.choose(_frame(prompt=prompt))

    assert intent == SelectCandidates((0, 2))


def test_rich_terminal_confirms_quit():
    terminal, _output = _terminal(["quit", "yes"])

    intent = terminal.choose(_frame())

    assert isinstance(intent, QuitGame)


def test_rich_terminal_declines_quit_and_keeps_prompting():
    terminal, _output = _terminal(["quit", "no", "1"])

    intent = terminal.choose(_frame())

    assert intent == SelectAction(0)


def test_rich_terminal_handles_display_commands_and_invalid_input():
    terminal, output = _terminal(["board", "hand", "help", "inspect nowhere", "bogus", "99", "1"])

    intent = terminal.choose(_frame())

    assert intent == SelectAction(0)
    rendered = output.getvalue()
    assert rendered.count("OPPONENT · PLAYER2") >= 2
    assert rendered.count("YOUR HAND") >= 2
    assert "Card not found" in rendered
    assert "Enter an action number or type help" in rendered
    assert "Action number must be between 1 and 1" in rendered


def test_rich_terminal_reprompts_for_invalid_candidate_selections():
    prompt = ChoicePromptView(
        min_count=1,
        max_count=2,
        allowed_counts=(1, 2),
        tips="Choose cards",
        candidates=(_card("C1", "First"), _card("C2", "Second")),
    )
    terminal, output = _terminal(["1 1", "9", "none", "2"])

    intent = terminal.choose(_frame(prompt=prompt))

    assert intent == SelectCandidates((1,))
    rendered = output.getvalue()
    assert "Candidate numbers must be unique" in rendered
    assert "Candidate numbers must be between 1 and 2" in rendered
    assert "Choose 1–2 cards" in rendered


def test_rich_terminal_accepts_an_empty_optional_choice():
    prompt = ChoicePromptView(
        min_count=0,
        max_count=1,
        allowed_counts=(0, 1),
        tips="Choose optional cards",
        candidates=(_card("C1", "First"),),
    )
    terminal, _output = _terminal([""])

    intent = terminal.choose(_frame(prompt=prompt))

    assert intent == SelectCandidates(())


def test_rich_terminal_renders_finished_and_aborted_results():
    terminal, output = _terminal([])

    terminal.show_result(
        SessionResult(
            status="finished",
            steps=10,
            reward=1.0,
            winner="player1",
            events=("Prize taken",),
        )
    )
    terminal.show_result(SessionResult(status="aborted", steps=3, reward=0, reason="quit"))

    rendered = output.getvalue()
    assert "Final events" in rendered
    assert "Winner: player1" in rendered
    assert "Game aborted after 3 steps (quit)" in rendered


def test_rich_terminal_uses_console_input_when_no_reader_is_injected(monkeypatch):
    output = StringIO()
    console = Console(file=output, color_system=None, width=80)
    monkeypatch.setattr(console, "input", lambda _prompt: "1")
    terminal = RichTerminal(console)

    intent = terminal.choose(_frame())

    assert intent == SelectAction(0)


def test_rich_terminal_wraps_key_content_at_narrow_width():
    terminal, output = _terminal(["1"], width=48)

    terminal.choose(_frame())

    lines = output.getvalue().splitlines()
    assert max(map(len, lines)) <= 48
    assert "LEGAL ACTIONS" in output.getvalue()


def test_rich_terminal_frames_board_regions_and_leaves_empty_cells_blank():
    terminal, output = _terminal(["1"])

    terminal.choose(_frame())

    rendered = output.getvalue()
    assert "╭─ OPPONENT · PLAYER2 " in rendered
    assert "╭─ STADIUM " in rendered
    assert "╭─ YOU · PLAYER1 " in rendered
    assert "—" not in rendered
