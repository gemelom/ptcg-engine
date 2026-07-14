import pytest

from ptcg.core.action import AttachEnergyAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("BRS-151")
@pytest.mark.card_coverage("BRS-151", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_double_turbo_energy_attaches_as_two_colorless_special_energy():
    double_turbo_energy = make_card("BRS-151")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[double_turbo_energy], active=[charmander]))

    actions = double_turbo_energy.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], AttachEnergyAction)
    assert actions[0].target is charmander

    double_turbo_energy.reduce_action(actions[0], state)

    assert double_turbo_energy in charmander.attachment
    assert charmander.energy == [CardType.COLORLESS, CardType.COLORLESS]
    assert double_turbo_energy not in state.player1.hand
    assert state.player1.energyPlayedTurn is True
    assert double_turbo_energy.get_actions(state) == []
