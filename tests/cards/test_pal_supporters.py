import pytest

from ptcg.core.action import UseSupporterAction
from ptcg.core.enums import PokemonPosition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAL-265")
@pytest.mark.card_coverage(
    "PAL-265",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_bosss_orders_switches_opponents_chosen_bench_with_active():
    bosss_orders = make_card("PAL-265")
    opponent_active = make_card("PAF-054")
    chosen_bench = make_card("PAF-007")
    other_bench = make_card("PAF-027")
    state = make_state(
        PlayerZones(hand=[bosss_orders]),
        PlayerZones(active=[opponent_active], bench=[chosen_bench, other_bench]),
    )

    actions = bosss_orders.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseSupporterAction)

    prompts = drive_choices(
        bosss_orders.reduce_action(actions[0], state),
        [lambda _info: [chosen_bench]],
    )

    assert prompts[0]["prompt"].source is bosss_orders
    assert prompts[0]["prompt"].candidates == [chosen_bench, other_bench]
    assert state.player2.active == [chosen_bench]
    assert state.player2.bench == [opponent_active, other_bench]
    assert chosen_bench.position == PokemonPosition.ACTIVE
    assert opponent_active.position == PokemonPosition.BENCH
    assert state.player1.discard == [bosss_orders]
    assert state.player1.supporterPlayedTurn is True


def test_bosss_orders_is_unavailable_without_opponents_benched_pokemon():
    bosss_orders = make_card("PAL-265")
    state = make_state(PlayerZones(hand=[bosss_orders]), PlayerZones(active=[make_card("PAF-054")]))

    assert bosss_orders.get_actions(state) == []


def test_bosss_orders_is_unavailable_after_supporter_played():
    bosss_orders = make_card("PAL-265")
    state = make_state(
        PlayerZones(hand=[bosss_orders]),
        PlayerZones(active=[make_card("PAF-054")], bench=[make_card("PAF-007")]),
    )
    state.player1.supporterPlayedTurn = True

    assert bosss_orders.get_actions(state) == []
