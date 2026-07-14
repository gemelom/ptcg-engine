import pytest

from ptcg.core.action import UseSupporterAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("OBF-186")
@pytest.mark.card_coverage(
    "OBF-186",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_arven_searches_item_and_tool_from_deck_to_hand(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    arven = make_card("OBF-186")
    item = make_card("PAF-084")
    tool = make_card("MEW-165")
    pokemon = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[arven], left=[item, tool, pokemon]))

    actions = arven.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseSupporterAction)

    prompts = drive_choices(
        arven.reduce_action(actions[0], state),
        [
            lambda _info: [item],
            lambda _info: [tool],
        ],
    )

    assert prompts[0]["prompt"].source is arven
    assert prompts[0]["prompt"].candidates == [item]
    assert prompts[1]["prompt"].source is arven
    assert prompts[1]["prompt"].candidates == [tool]
    assert state.player1.hand == [item, tool]
    assert state.player1.left == [pokemon]
    assert state.player1.discard == [arven]
    assert state.player1.supporterPlayedTurn is True


def test_arven_can_choose_no_matching_cards(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    arven = make_card("OBF-186")
    item = make_card("PAF-084")
    pokemon = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[arven], left=[item, pokemon]))

    prompts = drive_choices(
        arven.reduce_action(arven.get_actions(state)[0], state),
        [
            lambda _info: [],
            lambda _info: [],
        ],
    )

    assert prompts[0]["prompt"].candidates == [item]
    assert prompts[1]["prompt"].candidates == []
    assert state.player1.hand == []
    assert state.player1.left == [item, pokemon]
    assert state.player1.discard == [arven]


def test_arven_is_unavailable_after_supporter_played():
    arven = make_card("OBF-186")
    state = make_state(PlayerZones(hand=[arven]))
    state.player1.supporterPlayedTurn = True

    assert arven.get_actions(state) == []
