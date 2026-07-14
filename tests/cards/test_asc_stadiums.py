import pytest

from ptcg.core.action import DiscardStadiumAction, PutStadiumAction
from ptcg.core.enums import CardPosition, PlayerId
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("ASC-210")
@pytest.mark.card_coverage(
    "ASC-210",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
)
def test_team_rockets_watchtower_moves_from_hand_to_stadium():
    watchtower = make_card("ASC-210")
    state = make_state(PlayerZones(hand=[watchtower]))
    state.player1.firstTurn = False

    actions = watchtower.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], PutStadiumAction)

    watchtower.reduce_action(actions[0], state)

    assert state.stadium == [watchtower]
    assert watchtower not in state.player1.hand
    assert watchtower.cardPosition == CardPosition.STADIUM
    assert watchtower.playedFrom == PlayerId.PLAYER1


def test_team_rockets_watchtower_discards_to_player_who_played_it():
    watchtower = make_card("ASC-210")
    watchtower.playedFrom = PlayerId.PLAYER2
    state = make_state()
    state.stadium = [watchtower]

    watchtower.reduce_action(DiscardStadiumAction(PlayerId.PLAYER1, watchtower), state)

    assert state.stadium == []
    assert [card.name for card in state.player1.discard] == []
    assert [card.name for card in state.player2.discard] == ["Team Rocket's Watchtower"]


def test_team_rockets_watchtower_is_unavailable_on_first_turn():
    watchtower = make_card("ASC-210")
    state = make_state(PlayerZones(hand=[watchtower]))

    assert watchtower.get_actions(state) == []
