import pytest

from ptcg.core.action import AttachEnergyAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


def assert_basic_energy_attaches_once_per_turn(card_id, expected_type):
    charmander = make_card("PAF-007")
    energy = make_card(card_id)
    state = make_state(PlayerZones(hand=[energy], active=[charmander]))

    actions = energy.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], AttachEnergyAction)
    assert actions[0].target is charmander

    energy.reduce_action(actions[0], state)

    assert energy in charmander.attachment
    assert expected_type in charmander.energy
    assert energy not in state.player1.hand
    assert state.player1.energyPlayedTurn is True
    assert energy.get_actions(state) == []


@pytest.mark.card("SVE-002")
@pytest.mark.card_coverage("SVE-002", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_basic_fire_energy_attaches_to_current_pokemon_once_per_turn():
    assert_basic_energy_attaches_once_per_turn("SVE-002", CardType.FIRE)


@pytest.mark.card("SVE-004")
@pytest.mark.card_coverage("SVE-004", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_basic_lightning_energy_attaches_to_current_pokemon_once_per_turn():
    assert_basic_energy_attaches_once_per_turn("SVE-004", CardType.LIGHTNING)


@pytest.mark.card("SVE-005")
@pytest.mark.card_coverage("SVE-005", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_basic_psychic_energy_attaches_to_current_pokemon_once_per_turn():
    assert_basic_energy_attaches_once_per_turn("SVE-005", CardType.PSYCHIC)


@pytest.mark.card("SVE-007")
@pytest.mark.card_coverage("SVE-007", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_basic_darkness_energy_attaches_to_current_pokemon_once_per_turn():
    assert_basic_energy_attaches_once_per_turn("SVE-007", CardType.DARK)


@pytest.mark.card("SVE-008")
@pytest.mark.card_coverage("SVE-008", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_basic_metal_energy_attaches_to_current_pokemon_once_per_turn():
    assert_basic_energy_attaches_once_per_turn("SVE-008", CardType.METAL)
