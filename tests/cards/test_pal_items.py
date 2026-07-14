import pytest

from ptcg.core.action import UseItemAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAL-183")
@pytest.mark.card_coverage(
    "PAL-183",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "zone_change",
)
def test_great_ball_moves_selected_top_seven_pokemon_to_hand():
    great_ball = make_card("PAL-183")
    charmander = make_card("PAF-007")
    rare_candy = make_card("PAF-089")
    fire_energy = make_card("SVE-002")
    state = make_state(
        PlayerZones(
            hand=[great_ball],
            left=[rare_candy, fire_energy, charmander],
        )
    )

    actions = great_ball.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        great_ball.reduce_action(actions[0], state),
        [lambda _info: [charmander]],
    )

    assert prompts[0]["prompt"].source is great_ball
    assert [card.name for card in prompts[0]["prompt"].candidates] == ["Charmander"]
    assert great_ball in state.player1.discard
    assert charmander in state.player1.hand
    assert rare_candy in state.player1.left
    assert fire_energy in state.player1.left


@pytest.mark.card("PAL-189")
@pytest.mark.card_coverage(
    "PAL-189",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_superior_energy_retrieval_discards_two_cards_then_recovers_four_basic_energy():
    superior_energy_retrieval = make_card("PAL-189")
    discard_cost_1 = make_card("PAF-084")
    discard_cost_2 = make_card("PAF-089")
    fire_energy = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    psychic_energy = make_card("SVE-005")
    darkness_energy = make_card("SVE-007")
    metal_energy = make_card("SVE-008")
    non_energy = make_card("PAF-007")
    state = make_state(
        PlayerZones(
            hand=[superior_energy_retrieval, discard_cost_1, discard_cost_2],
            discard=[
                fire_energy,
                non_energy,
                lightning_energy,
                psychic_energy,
                darkness_energy,
                metal_energy,
            ],
        )
    )

    actions = superior_energy_retrieval.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        superior_energy_retrieval.reduce_action(actions[0], state),
        [
            lambda _info: [discard_cost_1, discard_cost_2],
            lambda _info: [fire_energy, lightning_energy, psychic_energy, darkness_energy],
        ],
    )

    assert prompts[0]["prompt"].source is superior_energy_retrieval
    assert prompts[0]["prompt"].candidates == [discard_cost_1, discard_cost_2]
    assert prompts[1]["prompt"].source is superior_energy_retrieval
    assert prompts[1]["prompt"].candidates == [
        fire_energy,
        lightning_energy,
        psychic_energy,
        darkness_energy,
        metal_energy,
    ]
    assert state.player1.hand == [fire_energy, lightning_energy, psychic_energy, darkness_energy]
    assert superior_energy_retrieval in state.player1.discard
    assert discard_cost_1 in state.player1.discard
    assert discard_cost_2 in state.player1.discard
    assert non_energy in state.player1.discard
    assert metal_energy in state.player1.discard


def test_superior_energy_retrieval_can_choose_no_energy_after_discarding_cost():
    superior_energy_retrieval = make_card("PAL-189")
    discard_cost_1 = make_card("PAF-084")
    discard_cost_2 = make_card("PAF-089")
    fire_energy = make_card("SVE-002")
    state = make_state(
        PlayerZones(
            hand=[superior_energy_retrieval, discard_cost_1, discard_cost_2],
            discard=[fire_energy],
        )
    )

    prompts = drive_choices(
        superior_energy_retrieval.reduce_action(
            superior_energy_retrieval.get_actions(state)[0], state
        ),
        [
            lambda _info: [discard_cost_1, discard_cost_2],
            lambda _info: [],
        ],
    )

    assert prompts[1]["prompt"].candidates == [fire_energy]
    assert state.player1.hand == []
    assert state.player1.discard == [
        fire_energy,
        discard_cost_1,
        discard_cost_2,
        superior_energy_retrieval,
    ]


def test_superior_energy_retrieval_is_unavailable_without_two_other_hand_cards():
    superior_energy_retrieval = make_card("PAL-189")
    discard_cost = make_card("PAF-084")
    state = make_state(PlayerZones(hand=[superior_energy_retrieval, discard_cost]))

    assert superior_energy_retrieval.get_actions(state) == []
