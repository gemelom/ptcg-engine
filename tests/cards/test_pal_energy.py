import pytest

from ptcg.core.action import AttachEnergyAction
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, SpecialCondition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAL-193")
@pytest.mark.card_coverage("PAL-193", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_therapeutic_energy_attaches_and_cures_relevant_special_condition():
    therapeutic_energy = make_card("PAL-193")
    charmander = make_card("PAF-007")
    charmander.specialCondition = SpecialCondition.ASLEEP
    state = make_state(PlayerZones(hand=[therapeutic_energy], active=[charmander]))

    actions = therapeutic_energy.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], AttachEnergyAction)
    assert actions[0].target is charmander

    therapeutic_energy.reduce_action(actions[0], state)

    assert therapeutic_energy in charmander.attachment
    assert CardType.COLORLESS in charmander.energy
    assert charmander.specialCondition == SpecialCondition.NONE
    assert therapeutic_energy not in state.player1.hand
    assert state.player1.energyPlayedTurn is True
    assert therapeutic_energy.get_actions(state) == []


@pytest.mark.card("PAL-190")
@pytest.mark.card_coverage(
    "PAL-190",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_jet_energy_attaches_to_active_then_switches_with_chosen_bench_pokemon():
    jet_energy = make_card("PAL-190")
    active = make_card("PAF-007")
    bench = make_card("PAF-027")
    state = make_state(PlayerZones(hand=[jet_energy], active=[active], bench=[bench]))

    actions = jet_energy.get_actions(state)
    active_actions = [action for action in actions if action.target is active]
    assert len(active_actions) == 1
    assert isinstance(active_actions[0], AttachEnergyAction)

    prompts = drive_choices(
        jet_energy.reduce_action(active_actions[0], state),
        [lambda _info: [bench]],
    )

    assert prompts[0]["prompt"].candidates == [bench]
    assert jet_energy in active.attachment
    assert CardType.COLORLESS in active.energy
    assert state.player1.active == [bench]
    assert state.player1.bench == [active]
    assert active.cardPosition == CardPosition.BENCH
    assert active.position == PokemonPosition.BENCH
    assert bench.cardPosition == CardPosition.ACTIVE
    assert bench.position == PokemonPosition.ACTIVE
    assert state.player1.energyPlayedTurn is True
    assert jet_energy.get_actions(state) == []
