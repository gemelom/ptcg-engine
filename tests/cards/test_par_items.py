import pytest

from ptcg.core.action import UseItemAction
from ptcg.core.enums import PokemonPosition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAR-160")
@pytest.mark.card_coverage(
    "PAR-160",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_counter_catcher_switches_opponents_chosen_bench_with_active_when_behind_on_prizes():
    counter_catcher = make_card("PAR-160")
    opponent_active = make_card("PAF-054")
    chosen_bench = make_card("PAF-007")
    other_bench = make_card("PAF-027")
    state = make_state(
        PlayerZones(
            hand=[counter_catcher],
            prize=[make_card("SVE-002"), make_card("SVE-004")],
        ),
        PlayerZones(
            prize=[make_card("SVE-005")],
            active=[opponent_active],
            bench=[chosen_bench, other_bench],
        ),
    )

    actions = counter_catcher.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        counter_catcher.reduce_action(actions[0], state),
        [lambda _info: [chosen_bench]],
    )

    assert prompts[0]["prompt"].source is counter_catcher
    assert prompts[0]["prompt"].candidates == [chosen_bench, other_bench]
    assert state.player2.active == [chosen_bench]
    assert state.player2.bench == [opponent_active, other_bench]
    assert chosen_bench.position == PokemonPosition.ACTIVE
    assert opponent_active.position == PokemonPosition.BENCH
    assert state.player1.discard == [counter_catcher]


def test_counter_catcher_is_unavailable_when_not_behind_on_prizes():
    counter_catcher = make_card("PAR-160")
    state = make_state(
        PlayerZones(hand=[counter_catcher], prize=[make_card("SVE-002")]),
        PlayerZones(
            prize=[make_card("SVE-004")],
            active=[make_card("PAF-054")],
            bench=[make_card("PAF-007")],
        ),
    )

    assert counter_catcher.get_actions(state) == []


def test_counter_catcher_is_unavailable_without_opponents_benched_pokemon():
    counter_catcher = make_card("PAR-160")
    state = make_state(
        PlayerZones(
            hand=[counter_catcher],
            prize=[make_card("SVE-002"), make_card("SVE-004")],
        ),
        PlayerZones(prize=[make_card("SVE-005")], active=[make_card("PAF-054")]),
    )

    assert counter_catcher.get_actions(state) == []


@pytest.mark.card("PAR-163")
@pytest.mark.card_coverage(
    "PAR-163",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_earthen_vessel_discards_one_card_then_searches_two_basic_energy(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    earthen_vessel = make_card("PAR-163")
    discard_cost = make_card("PAF-084")
    fire_energy = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    rare_candy = make_card("PAF-089")
    state = make_state(
        PlayerZones(
            hand=[earthen_vessel, discard_cost],
            left=[fire_energy, rare_candy, lightning_energy],
        )
    )

    actions = earthen_vessel.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        earthen_vessel.reduce_action(actions[0], state),
        [
            lambda _info: [discard_cost],
            lambda _info: [fire_energy, lightning_energy],
        ],
    )

    assert prompts[0]["prompt"].source is earthen_vessel
    assert prompts[0]["prompt"].candidates == [discard_cost]
    assert prompts[1]["prompt"].source is earthen_vessel
    assert prompts[1]["prompt"].candidates == [fire_energy, lightning_energy]
    assert state.player1.hand == [fire_energy, lightning_energy]
    assert state.player1.left == [rare_candy]
    assert state.player1.discard == [discard_cost, earthen_vessel]


def test_earthen_vessel_can_choose_no_energy_after_discarding_cost(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    earthen_vessel = make_card("PAR-163")
    discard_cost = make_card("PAF-084")
    fire_energy = make_card("SVE-002")
    state = make_state(
        PlayerZones(
            hand=[earthen_vessel, discard_cost],
            left=[fire_energy],
        )
    )

    prompts = drive_choices(
        earthen_vessel.reduce_action(earthen_vessel.get_actions(state)[0], state),
        [
            lambda _info: [discard_cost],
            lambda _info: [],
        ],
    )

    assert prompts[1]["prompt"].candidates == [fire_energy]
    assert state.player1.hand == []
    assert state.player1.left == [fire_energy]
    assert state.player1.discard == [discard_cost, earthen_vessel]


def test_earthen_vessel_is_unavailable_without_another_hand_card():
    earthen_vessel = make_card("PAR-163")
    state = make_state(PlayerZones(hand=[earthen_vessel]))

    assert earthen_vessel.get_actions(state) == []
