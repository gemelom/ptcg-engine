import pytest

from ptcg.core.action import AttachEnergyAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SIT-169")
@pytest.mark.card_coverage("SIT-169", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_v_guard_energy_attaches_as_colorless_special_energy():
    v_guard_energy = make_card("SIT-169")
    lugia = make_card("SIT-138")
    state = make_state(PlayerZones(hand=[v_guard_energy], active=[lugia]))

    actions = v_guard_energy.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], AttachEnergyAction)
    assert actions[0].target is lugia

    v_guard_energy.reduce_action(actions[0], state)

    assert v_guard_energy in lugia.attachment
    assert CardType.COLORLESS in lugia.energy
    assert v_guard_energy not in state.player1.hand
    assert state.player1.energyPlayedTurn is True
    assert v_guard_energy.get_actions(state) == []
