import pytest

from ptcg.core.action import UseItemAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("CRZ-127")
@pytest.mark.card_coverage(
    "CRZ-127",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_energy_retrieval_moves_up_to_two_basic_energy_from_discard_to_hand():
    energy_retrieval = make_card("CRZ-127")
    fire_energy = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    ultra_ball = make_card("PAF-091")
    state = make_state(
        PlayerZones(
            hand=[energy_retrieval],
            discard=[fire_energy, lightning_energy, ultra_ball],
        )
    )

    actions = energy_retrieval.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        energy_retrieval.reduce_action(actions[0], state),
        [lambda _info: [fire_energy, lightning_energy]],
    )

    assert prompts[0]["prompt"].source is energy_retrieval
    assert sorted(card.name for card in prompts[0]["prompt"].candidates) == [
        "Fire Energy",
        "Lightning Energy",
    ]
    assert energy_retrieval in state.player1.discard
    assert ultra_ball in state.player1.discard
    assert fire_energy in state.player1.hand
    assert lightning_energy in state.player1.hand


def test_energy_retrieval_is_unavailable_without_basic_energy_in_discard():
    energy_retrieval = make_card("CRZ-127")
    ultra_ball = make_card("PAF-091")
    state = make_state(PlayerZones(hand=[energy_retrieval], discard=[ultra_ball]))

    assert energy_retrieval.get_actions(state) == []


@pytest.mark.card("CRZ-135")
@pytest.mark.card_coverage(
    "CRZ-135",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_lost_vacuum_lost_zones_hand_card_then_attached_tool():
    lost_vacuum = make_card("CRZ-135")
    fire_energy = make_card("SVE-002")
    charmander = make_card("PAF-007")
    rigid_band = make_card("MEW-165")
    charmander.attachment = [rigid_band]
    state = make_state(PlayerZones(hand=[lost_vacuum, fire_energy], active=[charmander]))

    actions = lost_vacuum.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        lost_vacuum.reduce_action(actions[0], state),
        [
            lambda _info: [fire_energy],
            lambda _info: [charmander],
        ],
    )

    assert prompts[0]["prompt"].source is lost_vacuum
    assert prompts[0]["prompt"].candidates == [fire_energy]
    assert prompts[1]["prompt"].source is lost_vacuum
    assert prompts[1]["prompt"].candidates == [charmander]
    assert lost_vacuum in state.player1.discard
    assert fire_energy in state.player1.lostZone
    assert rigid_band in state.player1.lostZone
    assert rigid_band not in charmander.attachment


def test_lost_vacuum_is_unavailable_without_extra_hand_card():
    lost_vacuum = make_card("CRZ-135")
    charmander = make_card("PAF-007")
    charmander.attachment = [make_card("MEW-165")]
    state = make_state(PlayerZones(hand=[lost_vacuum], active=[charmander]))

    assert lost_vacuum.get_actions(state) == []
