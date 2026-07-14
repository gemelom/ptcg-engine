import pytest

from ptcg.core.action import DiscardStadiumAction, PutStadiumAction, UseStadiumAction
from ptcg.core.enums import CardPosition, PlayerId
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("OBF-196")
@pytest.mark.card_coverage(
    "OBF-196",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_town_store_moves_from_hand_to_stadium():
    town_store = make_card("OBF-196")
    state = make_state(PlayerZones(hand=[town_store]))

    actions = town_store.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], PutStadiumAction)

    list(town_store.reduce_action(actions[0], state))

    assert state.stadium == [town_store]
    assert town_store not in state.player1.hand
    assert town_store.cardPosition == CardPosition.STADIUM
    assert town_store.playedFrom == PlayerId.PLAYER1
    assert state.player1.stadiumPlayedTurn is True


def test_town_store_searches_tool_from_deck_to_hand(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    town_store = make_card("OBF-196")
    tool = make_card("MEW-165")
    item = make_card("PAF-084")
    state = make_state(PlayerZones(left=[item, tool]))
    state.stadium = [town_store]

    actions = town_store.get_actions(state)
    use_actions = [action for action in actions if isinstance(action, UseStadiumAction)]
    assert len(use_actions) == 1

    prompts = drive_choices(
        town_store.reduce_action(use_actions[0], state),
        [lambda _info: [tool]],
    )

    assert prompts[0]["prompt"].source is town_store
    assert prompts[0]["prompt"].candidates == [tool]
    assert state.player1.hand == [tool]
    assert state.player1.left == [item]
    assert state.player1.stadiumUsedTurn is True


def test_town_store_search_is_unavailable_without_tool_in_deck():
    town_store = make_card("OBF-196")
    state = make_state(PlayerZones(left=[make_card("PAF-084")]))
    state.stadium = [town_store]

    assert [
        action for action in town_store.get_actions(state) if isinstance(action, UseStadiumAction)
    ] == []


def test_town_store_is_unavailable_after_stadium_played_this_turn():
    town_store = make_card("OBF-196")
    state = make_state(PlayerZones(hand=[town_store]))
    state.player1.stadiumPlayedTurn = True

    assert town_store.get_actions(state) == []


def test_town_store_discards_to_player_who_played_it():
    town_store = make_card("OBF-196")
    town_store.playedFrom = PlayerId.PLAYER2
    state = make_state()
    state.stadium = [town_store]

    list(town_store.reduce_action(DiscardStadiumAction(PlayerId.PLAYER1, town_store), state))

    assert state.stadium == []
    assert state.player1.discard == []
    assert [card.name for card in state.player2.discard] == ["Town Store"]
