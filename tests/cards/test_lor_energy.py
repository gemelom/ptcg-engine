import pytest

from ptcg.core.action import AttachEnergyAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("LOR-171")
@pytest.mark.card_coverage("LOR-171", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_gift_energy_attaches_as_colorless_special_energy():
    gift_energy = make_card("LOR-171")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[gift_energy], active=[charmander]))

    actions = gift_energy.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], AttachEnergyAction)
    assert actions[0].target is charmander

    gift_energy.reduce_action(actions[0], state)

    assert gift_energy in charmander.attachment
    assert CardType.COLORLESS in charmander.energy
    assert gift_energy not in state.player1.hand
    assert state.player1.energyPlayedTurn is True
    assert gift_energy.get_actions(state) == []
