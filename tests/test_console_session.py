from __future__ import annotations

from collections.abc import Sequence

import pytest

from ptcg.console.model import (
    DecisionFrame,
    PlayConfig,
    QuitGame,
    SelectAction,
    SelectCandidates,
    SessionResult,
)
from ptcg.console.session import run_interactive
from ptcg.core.action import ChooseCardAction, ChooseCardActionSpace, ChooseCardPrompt, PassTurn
from ptcg.core.enums import PlayerId
from tests.helpers.cards import make_card


def _player_observation(
    player_id: str,
    *,
    hand: list[dict] | None,
) -> dict:
    return {
        "id": player_id,
        "active": [],
        "bench": [],
        "hand": hand,
        "hand_count": len(hand or []),
        "deck_count": 40,
        "prize_count": 6,
        "discard": [],
        "lost_zone": [],
    }


def _safe_observation() -> dict:
    return {
        "viewer": "player1",
        "turn": "player1",
        "timestep": 1,
        "turn_number": 1,
        "is_choosing_card": False,
        "stadium": [],
        "self": _player_observation(
            "player1",
            hand=[{"name": "Charmander", "set_name": "PAF", "number": "007"}],
        ),
        "opponent": _player_observation("player2", hand=None),
        "auto_events": [],
        "termination_reason": None,
    }


class ScriptedTerminal:
    def __init__(self, intents: Sequence[object]) -> None:
        self.intents = iter(intents)
        self.frames: list[DecisionFrame] = []
        self.errors: list[str] = []
        self.result: SessionResult | None = None

    def choose(self, frame: DecisionFrame):
        self.frames.append(frame)
        return next(self.intents)

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def show_result(self, result: SessionResult) -> None:
        self.result = result


class RoutingEnvironment:
    def __init__(self) -> None:
        self.winner = PlayerId.PLAYER1
        self.recorder = None
        self.observed_as: list[PlayerId] = []
        self.bot_action = PassTurn(PlayerId.PLAYER2, object())
        self.human_action = PassTurn(PlayerId.PLAYER1, object())
        self.step_count = 0

    def reset(self):
        unsafe_observation = {"opponent_hand": "SECRET OPPONENT CARD"}
        info = {
            "raw_available_actions": [self.bot_action],
            "turn": PlayerId.PLAYER2,
            "auto_executed": [],
        }
        return unsafe_observation, 0.0, False, info

    def observe(self, viewer_id: PlayerId):
        self.observed_as.append(viewer_id)
        return _safe_observation()

    def step(self, action):
        self.step_count += 1
        if self.step_count == 1:
            assert action is self.bot_action
            return (
                {},
                0.0,
                False,
                {
                    "raw_available_actions": [self.human_action],
                    "turn": PlayerId.PLAYER1,
                    "auto_executed": ["Coin flip: HEADS"],
                },
            )
        assert action is self.human_action
        return (
            {},
            1.0,
            True,
            {
                "raw_available_actions": [],
                "turn": PlayerId.PLAYER1,
                "auto_executed": [],
                "winner": PlayerId.PLAYER1,
                "termination_reason": "all_prizes_taken",
            },
        )


def test_session_auto_advances_opponent_and_uses_fixed_human_observation():
    env = RoutingEnvironment()
    terminal = ScriptedTerminal([SelectAction(0)])

    result = run_interactive(
        PlayConfig(opponent_policy="first"),
        terminal,
        env=env,
    )

    assert result.status == "finished"
    assert result.winner == "player1"
    assert env.observed_as == [PlayerId.PLAYER1]
    assert len(terminal.frames) == 1
    rendered_data = repr(terminal.frames[0])
    assert "SECRET OPPONENT CARD" not in rendered_data
    assert "Player2 passed the turn" in rendered_data
    assert "Coin flip: HEADS" in rendered_data


def test_session_reprompts_for_an_intent_that_does_not_match_the_decision():
    env = RoutingEnvironment()
    terminal = ScriptedTerminal([SelectCandidates((0,)), SelectAction(99), SelectAction(0)])

    result = run_interactive(PlayConfig(opponent_policy="first"), terminal, env=env)

    assert result.status == "finished"
    assert terminal.errors == [
        "Card candidates are not expected for this decision.",
        "Action number must be between 1 and 1.",
    ]


def test_session_allows_the_human_to_quit():
    env = RoutingEnvironment()
    terminal = ScriptedTerminal([QuitGame()])

    result = run_interactive(PlayConfig(opponent_policy="first"), terminal, env=env)

    assert result.status == "aborted"
    assert result.reason == "quit"
    assert result.exit_code == 1


@pytest.mark.parametrize(
    ("error", "reason", "exit_code"),
    [(EOFError(), "eof", 1), (KeyboardInterrupt(), "interrupt", 130)],
)
def test_session_handles_closed_or_interrupted_input(error, reason, exit_code):
    class RaisingTerminal(ScriptedTerminal):
        def choose(self, frame):
            raise error

    result = run_interactive(
        PlayConfig(opponent_policy="first"),
        RaisingTerminal([]),
        env=RoutingEnvironment(),
    )

    assert result.status == "aborted"
    assert result.reason == reason
    assert result.exit_code == exit_code


def test_session_stops_at_the_engine_step_limit():
    terminal = ScriptedTerminal([])

    result = run_interactive(
        PlayConfig(opponent_policy="first", max_steps=1),
        terminal,
        env=RoutingEnvironment(),
    )

    assert result.status == "stopped"
    assert result.reason == "max_steps"
    assert result.steps == 1


@pytest.mark.parametrize("during_reset", [True, False])
def test_session_handles_interrupts_during_engine_work(during_reset):
    class InterruptingEnvironment(RoutingEnvironment):
        def reset(self):
            if during_reset:
                raise KeyboardInterrupt
            return super().reset()

        def step(self, action):
            raise KeyboardInterrupt

    terminal = ScriptedTerminal([])

    result = run_interactive(
        PlayConfig(opponent_policy="first"),
        terminal,
        env=InterruptingEnvironment(),
    )

    assert result.status == "aborted"
    assert result.reason == "interrupt"
    assert result.exit_code == 130


def test_session_reports_missing_actions_as_an_engine_error():
    class NoActionsEnvironment(RoutingEnvironment):
        def reset(self):
            return {}, 0.0, False, {"raw_available_actions": [], "auto_executed": []}

    terminal = ScriptedTerminal([])

    result = run_interactive(PlayConfig(), terminal, env=NoActionsEnvironment())

    assert result.status == "error"
    assert result.reason == "no_available_actions"
    assert result.exit_code == 2


@pytest.mark.parametrize(
    "config",
    [PlayConfig(opponent_policy="unknown"), PlayConfig(max_steps=0)],
)
def test_session_validates_programmatic_configuration(config):
    with pytest.raises(ValueError):
        run_interactive(config, ScriptedTerminal([]), env=RoutingEnvironment())


class NonIterableChoiceSpace(ChooseCardActionSpace):
    def __iter__(self):
        raise AssertionError("The interactive session must not enumerate choice combinations")


class ChoiceEnvironment:
    def __init__(self) -> None:
        self.winner = PlayerId.PLAYER1
        self.recorder = None
        self.candidates = [make_card("SVE-002") for _ in range(30)]
        self.actions = NonIterableChoiceSpace(
            PlayerId.PLAYER1,
            PlayerId.PLAYER1,
            1,
            30,
            self.candidates,
        )
        self.prompt = ChooseCardPrompt(1, 30, self.candidates, tips="Choose cards")
        self.received: ChooseCardAction | None = None

    def reset(self):
        return (
            {},
            0.0,
            False,
            {
                "raw_available_actions": self.actions,
                "prompt": self.prompt,
                "turn": PlayerId.PLAYER1,
                "auto_executed": [],
            },
        )

    def observe(self, viewer_id: PlayerId):
        assert viewer_id == PlayerId.PLAYER1
        return _safe_observation()

    def step(self, action):
        self.received = action
        return (
            {},
            1.0,
            True,
            {
                "raw_available_actions": [],
                "turn": PlayerId.PLAYER1,
                "auto_executed": [],
                "winner": PlayerId.PLAYER1,
            },
        )


def test_session_maps_candidate_indices_without_expanding_choice_space():
    env = ChoiceEnvironment()
    terminal = ScriptedTerminal([SelectCandidates((29, 0))])

    result = run_interactive(PlayConfig(), terminal, env=env)

    assert result.status == "finished"
    assert env.received is not None
    assert env.received.chosen == [env.candidates[0], env.candidates[29]]


def test_session_masks_hidden_choice_candidates_and_events():
    env = ChoiceEnvironment()
    env.actions = NonIterableChoiceSpace(
        PlayerId.PLAYER1,
        PlayerId.PLAYER1,
        1,
        1,
        env.candidates,
        hidden=True,
    )
    env.prompt = ChooseCardPrompt(
        1,
        1,
        env.candidates,
        hidden=True,
        tips="Choose a Prize card",
    )
    terminal = ScriptedTerminal([SelectCandidates((0,))])

    result = run_interactive(PlayConfig(), terminal, env=env)

    assert "Fire Energy" not in repr(terminal.frames[0].prompt)
    assert terminal.frames[0].prompt.candidates[0].name == "Hidden card 1"
    assert "Fire Energy" not in " ".join(result.events)
    assert "1 hidden card" in " ".join(result.events)


def test_session_reprompts_when_an_action_number_is_used_for_a_card_choice():
    env = ChoiceEnvironment()
    terminal = ScriptedTerminal([SelectAction(0), SelectCandidates((0,))])

    result = run_interactive(PlayConfig(), terminal, env=env)

    assert result.status == "finished"
    assert terminal.errors == ["Choose candidate numbers for this card prompt."]


class ListedChoiceEnvironment(ChoiceEnvironment):
    def __init__(self) -> None:
        super().__init__()
        self.candidates = [make_card("SVE-002"), make_card("SVE-005")]
        self.actions = [
            ChooseCardAction(
                PlayerId.PLAYER1,
                PlayerId.PLAYER1,
                [candidate],
                self.candidates,
            )
            for candidate in self.candidates
        ]
        self.prompt = ChooseCardPrompt(0, 2, self.candidates, tips="Discard energy")


def test_session_uses_actual_legal_counts_for_materialized_card_choices():
    env = ListedChoiceEnvironment()
    terminal = ScriptedTerminal([SelectCandidates((1,))])

    result = run_interactive(PlayConfig(), terminal, env=env)

    assert result.status == "finished"
    assert terminal.frames[0].prompt is not None
    assert terminal.frames[0].prompt.allowed_counts == (1,)
    assert env.received is env.actions[1]


class AlwaysFirstTerminal(ScriptedTerminal):
    def __init__(self) -> None:
        super().__init__([])

    def choose(self, frame: DecisionFrame):
        self.frames.append(frame)
        if frame.prompt is not None:
            return SelectCandidates(tuple(range(frame.prompt.allowed_counts[0])))
        return SelectAction(0)


def test_session_completes_a_real_deterministic_match():
    terminal = AlwaysFirstTerminal()

    result = run_interactive(
        PlayConfig(
            deck="charizard_ex",
            opponent_deck="miraidon_ex",
            opponent_policy="first",
            seed=42,
            max_steps=1000,
        ),
        terminal,
    )

    assert result.status == "finished"
    assert result.steps <= 1000
    assert terminal.frames
    assert terminal.result == result
