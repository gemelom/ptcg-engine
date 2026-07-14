import pytest

from ptcg.core.action import UseSupporterAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("TEF-145")
@pytest.mark.card_coverage(
    "TEF-145",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_ciphermaniacs_codebreaking_puts_two_chosen_cards_on_top_of_deck():
    card = make_card("TEF-145")
    deck1 = make_card("PAF-007")
    deck2 = make_card("PAF-008")
    deck3 = make_card("SVE-002")
    state = make_state(PlayerZones(hand=[card], left=[deck1, deck2, deck3]))
    state.player1.firstTurn = False

    actions = card.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseSupporterAction)

    drive_choices(
        card.reduce_action(actions[0], state),
        [lambda _info: [deck1, deck2], lambda _info: [deck1]],
    )

    assert state.player1.left[0] is deck1
    assert state.player1.left[1] is deck2
    assert card in state.player1.discard
    assert state.player1.supporterPlayedTurn is True


def test_ciphermaniacs_codebreaking_unavailable_on_first_turn():
    card = make_card("TEF-145")
    state = make_state(PlayerZones(hand=[card], left=[make_card("PAF-007"), make_card("PAF-008")]))
    state.player1.firstTurn = True

    assert card.get_actions(state) == []


def test_ciphermaniacs_codebreaking_unavailable_when_supporter_played():
    card = make_card("TEF-145")
    state = make_state(PlayerZones(hand=[card], left=[make_card("PAF-007"), make_card("PAF-008")]))
    state.player1.supporterPlayedTurn = True

    assert card.get_actions(state) == []


@pytest.mark.card("TEF-155")
@pytest.mark.card_coverage(
    "TEF-155",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_mortys_conviction_draws_cards_equal_to_opponent_bench():
    card = make_card("TEF-155")
    discard_cost = make_card("SVE-002")
    deck_cards = [make_card("PAF-007"), make_card("PAF-008"), make_card("SVE-004")]
    opp_bench = [make_card("SIT-138"), make_card("PAF-054")]
    state = make_state(
        PlayerZones(hand=[card, discard_cost], left=deck_cards),
        PlayerZones(active=[make_card("PAF-007")], bench=opp_bench),
    )

    actions = card.get_actions(state)
    assert len(actions) == 1

    drive_choices(
        card.reduce_action(actions[0], state),
        [lambda _info: [discard_cost]],
    )

    assert len(state.player1.hand) == 2  # drew 2 for 2 benched
    assert discard_cost in state.player1.discard
    assert card in state.player1.discard
    assert state.player1.supporterPlayedTurn is True


def test_mortys_conviction_unavailable_without_opponent_bench():
    card = make_card("TEF-155")
    extra = make_card("SVE-002")
    state = make_state(
        PlayerZones(hand=[card, extra]),
        PlayerZones(active=[make_card("PAF-007")]),
    )

    assert card.get_actions(state) == []
