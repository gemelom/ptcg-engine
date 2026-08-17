from __future__ import annotations

import pytest

from ptcg.core.action import PassTurn
from ptcg.core.enums import PlayerId
from ptcg.core.exceptions import GameTermination
from ptcg.utils.utils import current_player, judge_termination, next_turn, opponent_player
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


def _state_with_decks(*, current_deck_size: int, opponent_deck_size: int):
    return make_state(
        PlayerZones(
            left=[make_card("SVE-002") for _ in range(current_deck_size)],
            prize=[make_card("SVE-004")],
            active=[make_card("PAF-007")],
        ),
        PlayerZones(
            left=[make_card("SVE-005") for _ in range(opponent_deck_size)],
            prize=[make_card("SVE-007")],
            active=[make_card("PAF-027")],
        ),
    )


def test_empty_deck_does_not_end_game_until_that_player_must_draw():
    state = _state_with_decks(current_deck_size=0, opponent_deck_size=2)

    assert judge_termination(state) == (False, None)

    next_turn(state)

    assert state.turn == PlayerId.PLAYER2
    assert len(state.player2.left) == 1
    assert judge_termination(state) == (False, None)


def test_player_loses_when_their_turn_starts_with_no_card_to_draw():
    state = _state_with_decks(current_deck_size=2, opponent_deck_size=0)
    winner = current_player(state)
    loser = opponent_player(state)

    with pytest.raises(GameTermination):
        next_turn(state)

    assert state.turn == loser.id
    assert state.termination_reason == "deck_out"
    assert judge_termination(state) == (True, winner.id)


def test_pass_turn_reports_deck_out_through_environment_result():
    from ptcg import PokemonTCG

    env = PokemonTCG(seed=42, record_game=False)
    _obs, _reward, _done, info = env.reset()
    for _ in range(2):
        _obs, _reward, _done, info = env.step(info["raw_available_actions"][0])

    state = env.gamestate
    opponent_player(state).left.clear()
    pass_turn = next(
        action for action in info["raw_available_actions"] if isinstance(action, PassTurn)
    )

    _obs, _reward, done, info = env.step(pass_turn)

    assert done is True
    assert info["winner"] == pass_turn.playerId
    assert info["termination_reason"] == "deck_out"
