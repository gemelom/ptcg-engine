from __future__ import annotations

from ptcg.core.action import PutStadiumAction, UseSupporterAction
from ptcg.core.enums import PlayerId
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state

P1 = PlayerId.PLAYER1
P2 = PlayerId.PLAYER2


def _supporter_actions(player, state):
    return [
        action for action in player.get_actions(state) if isinstance(action, UseSupporterAction)
    ]


def _stadium_actions(player, state):
    return [action for action in player.get_actions(state) if isinstance(action, PutStadiumAction)]


def test_second_player_may_use_ciphermaniac_on_first_turn():
    ciphermaniac = make_card("TEF-145")
    state = make_state(
        PlayerZones(active=[make_card("PAF-007")], hand=[ciphermaniac], left=[make_card("SVE-002") for _ in range(10)]),
        PlayerZones(active=[make_card("PAF-007")]),
        first_player_id=P2,
    )
    state.player1.firstTurn = True
    state.player1.supporterPlayedTurn = False
    assert _supporter_actions(state.player1, state), "second player must be able to play a Supporter on turn 1"


def test_first_player_stays_locked_out_of_supporters():
    ciphermaniac = make_card("TEF-145")
    state = make_state(
        PlayerZones(active=[make_card("PAF-007")], hand=[ciphermaniac], left=[make_card("SVE-002") for _ in range(10)]),
        PlayerZones(active=[make_card("PAF-007")]),
        first_player_id=P1,
    )
    state.player1.firstTurn = True
    state.player1.supporterPlayedTurn = True  # environment applies the opening lock
    assert not _supporter_actions(state.player1, state)


def test_stadium_has_no_first_turn_restriction():
    watchtower = make_card("ASC-210")
    state = make_state(
        PlayerZones(active=[make_card("PAF-007")], hand=[watchtower]),
        PlayerZones(active=[make_card("PAF-007")]),
        first_player_id=P1,
    )
    state.player1.firstTurn = True
    state.player1.stadiumPlayedTurn = False
    assert _stadium_actions(state.player1, state), "Stadium cards may be played on turn 1"


def test_stadium_is_once_per_turn():
    watchtower = make_card("ASC-210")
    state = make_state(
        PlayerZones(active=[make_card("PAF-007")], hand=[watchtower]),
        PlayerZones(active=[make_card("PAF-007")]),
        first_player_id=P1,
    )
    state.player1.stadiumPlayedTurn = True
    assert not _stadium_actions(state.player1, state)
