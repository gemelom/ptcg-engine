import pytest

from ptcg.core.action import UseItemAction
from ptcg.core.enums import CardPosition, PokemonPosition
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("ASR-154")
@pytest.mark.card_coverage(
    "ASR-154",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
)
def test_switch_cart_switches_active_basic_with_bench_and_heals_moved_pokemon():
    switch_cart = make_card("ASR-154")
    active = make_card("ASR-046")
    active.hp = 100
    benched = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[switch_cart], active=[active], bench=[benched]))

    actions = switch_cart.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    switch_cart.reduce_action(actions[0], state)

    assert switch_cart in state.player1.discard
    assert state.player1.active == [benched]
    assert state.player1.bench == [active]
    assert active.hp == 130
    assert active.cardPosition == CardPosition.BENCH
    assert active.position == PokemonPosition.BENCH
    assert benched.cardPosition == CardPosition.ACTIVE
    assert benched.position == PokemonPosition.ACTIVE


def test_switch_cart_is_unavailable_without_benched_pokemon():
    switch_cart = make_card("ASR-154")
    active = make_card("ASR-046")
    state = make_state(PlayerZones(hand=[switch_cart], active=[active]))

    assert switch_cart.get_actions(state) == []


def test_switch_cart_is_unavailable_when_active_is_not_basic():
    switch_cart = make_card("ASR-154")
    active = make_card("PAF-054")
    benched = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[switch_cart], active=[active], bench=[benched]))

    assert switch_cart.get_actions(state) == []
