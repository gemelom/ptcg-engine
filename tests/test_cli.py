from __future__ import annotations

import pytest

from ptcg import cli
from ptcg.console.model import SessionResult


def test_play_parser_uses_confirmed_defaults():
    args = cli.build_play_parser().parse_args([])

    assert args.deck is None
    assert args.opponent_deck is None
    assert args.opponent_policy == "random"
    assert args.seed == 0
    assert args.max_steps == 1000


def test_main_dispatches_play_subcommand(monkeypatch):
    captured = {}

    def fake_run_interactive(config, terminal):
        captured["config"] = config
        captured["terminal"] = terminal
        return SessionResult(status="finished", steps=3, reward=1.0, winner="player1")

    monkeypatch.setattr("ptcg.console.run_interactive", fake_run_interactive)

    exit_code = cli.main(
        [
            "play",
            "--deck",
            "charizard_ex",
            "--opponent-deck",
            "miraidon_ex",
            "--opponent-policy",
            "first",
            "--seed",
            "7",
        ]
    )

    assert exit_code == 0
    assert captured["config"].deck == "charizard_ex"
    assert captured["config"].opponent_deck == "miraidon_ex"
    assert captured["config"].opponent_policy == "first"
    assert captured["config"].seed == 7


def test_main_keeps_legacy_simulation_dispatch(monkeypatch):
    captured = {}

    def fake_run(args):
        captured["args"] = args
        return 17

    monkeypatch.setattr(cli, "run", fake_run)

    exit_code = cli.main(["--deck1", "charizard_ex", "--policy", "first", "--quiet"])

    assert exit_code == 17
    assert captured["args"].deck1 == "charizard_ex"
    assert captured["args"].policy == "first"
    assert captured["args"].quiet is True


def test_play_parser_rejects_a_non_positive_step_limit():
    with pytest.raises(SystemExit):
        cli.build_play_parser().parse_args(["--max-steps", "0"])
