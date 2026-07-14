import pytest

from ptcg.core.action import UseToolAction
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("TEF-151")
@pytest.mark.card_coverage(
    "TEF-151",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
)
def test_heavy_baton_attaches_to_pokemon():
    baton = make_card("TEF-151")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[baton], active=[charmander]))

    actions = baton.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseToolAction)
    assert actions[0].target is charmander

    baton.reduce_action(actions[0], state)

    assert baton.hasAttached is True
    assert baton.attachedTo == [charmander]
    assert baton not in state.player1.hand


def test_heavy_baton_unavailable_after_attachment():
    baton = make_card("TEF-151")
    baton.hasAttached = True
    state = make_state(PlayerZones(active=[make_card("PAF-007")]))

    assert baton.get_actions(state) == []


@pytest.mark.card("TEF-159")
@pytest.mark.card_coverage(
    "TEF-159",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
)
def test_rescue_board_attaches_to_pokemon():
    board = make_card("TEF-159")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[board], active=[charmander]))

    actions = board.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseToolAction)

    board.reduce_action(actions[0], state)

    assert board.hasAttached is True
    assert board.attachedTo == [charmander]
    assert board not in state.player1.hand


def test_rescue_board_unavailable_after_attachment():
    board = make_card("TEF-159")
    board.hasAttached = True
    state = make_state(PlayerZones(active=[make_card("PAF-007")]))

    assert board.get_actions(state) == []
