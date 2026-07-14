import pytest

from ptcg.core.action import UseItemAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("TEF-144")
@pytest.mark.card_coverage(
    "TEF-144",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_buddy_buddy_poffin_puts_two_small_basics_on_bench():
    card = make_card("TEF-144")
    small1 = make_card("TEF-128")   # Dunsparce - 60 HP Basic
    small2 = make_card("BRS-124")   # Minccino - Basic <=70 HP
    big = make_card("PAF-054")      # Charizard ex - too big
    state = make_state(PlayerZones(hand=[card], left=[small1, small2, big]))

    actions = card.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        card.reduce_action(actions[0], state),
        [lambda _info: [small1, small2]],
    )

    assert prompts[0]["prompt"].source is card
    assert set(prompts[0]["prompt"].candidates) == {small1, small2}
    assert small1 in state.player1.bench
    assert small2 in state.player1.bench
    assert big not in state.player1.bench
    assert card in state.player1.discard


def test_buddy_buddy_poffin_unavailable_when_bench_full():
    card = make_card("TEF-144")
    bench = [make_card("PAF-007") for _ in range(5)]
    state = make_state(PlayerZones(hand=[card], left=[make_card("TEF-128")], bench=bench))

    assert card.get_actions(state) == []


@pytest.mark.card("TEF-153")
@pytest.mark.card_coverage(
    "TEF-153",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_master_ball_discards_hand_card_and_searches_pokemon():
    card = make_card("TEF-153")
    discard_cost = make_card("SVE-002")
    target_pokemon = make_card("PAF-007")
    other_deck = make_card("PAF-084")
    state = make_state(
        PlayerZones(hand=[card, discard_cost], left=[target_pokemon, other_deck])
    )

    actions = card.get_actions(state)
    assert len(actions) == 1

    drive_choices(
        card.reduce_action(actions[0], state),
        [lambda _info: [discard_cost], lambda _info: [target_pokemon]],
    )

    assert target_pokemon in state.player1.hand
    assert discard_cost in state.player1.discard
    assert card in state.player1.discard


def test_master_ball_unavailable_with_only_one_card_in_hand():
    card = make_card("TEF-153")
    state = make_state(PlayerZones(hand=[card], left=[make_card("PAF-007")]))

    assert card.get_actions(state) == []


@pytest.mark.card("TEF-157")
@pytest.mark.card_coverage(
    "TEF-157",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_prime_catcher_switches_opponent_bench_and_player_bench():
    card = make_card("TEF-157")
    my_active = make_card("PAF-007")
    my_bench = make_card("PAF-008")
    opp_active = make_card("PAF-054")
    opp_bench = make_card("SIT-138")
    state = make_state(
        PlayerZones(hand=[card], active=[my_active], bench=[my_bench]),
        PlayerZones(active=[opp_active], bench=[opp_bench]),
    )

    actions = card.get_actions(state)
    assert len(actions) == 1

    drive_choices(
        card.reduce_action(actions[0], state),
        [lambda _info: [opp_bench], lambda _info: [my_bench]],
    )

    assert state.player2.active[0] is opp_bench
    assert opp_active in state.player2.bench
    assert state.player1.active[0] is my_bench
    assert my_active in state.player1.bench
    assert card in state.player1.discard


def test_prime_catcher_unavailable_without_own_bench():
    card = make_card("TEF-157")
    state = make_state(
        PlayerZones(hand=[card], active=[make_card("PAF-007")]),
        PlayerZones(active=[make_card("PAF-054")], bench=[make_card("SIT-138")]),
    )

    assert card.get_actions(state) == []
