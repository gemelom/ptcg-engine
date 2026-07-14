import pytest

from ptcg.core.action import UseToolAction
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SVI-169")
@pytest.mark.card_coverage(
    "SVI-169",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
)
def test_defiance_band_attaches_to_pokemon():
    band = make_card("SVI-169")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[band], active=[charmander]))

    actions = band.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseToolAction)
    assert actions[0].target is charmander

    band.reduce_action(actions[0], state)

    assert band.hasAttached is True
    assert band.attachedTo == [charmander]
    assert band not in state.player1.hand


def test_defiance_band_unavailable_after_attachment():
    band = make_card("SVI-169")
    charmander = make_card("PAF-007")
    band.hasAttached = True
    band.attachedTo = [charmander]
    state = make_state(PlayerZones(active=[charmander]))

    assert band.get_actions(state) == []
