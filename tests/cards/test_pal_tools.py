import pytest

from ptcg.core.action import UseToolAction
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAL-173")
@pytest.mark.card_coverage(
    "PAL-173",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
)
def test_bravery_charm_attaches_to_basic_pokemon_and_adds_hp():
    bravery_charm = make_card("PAL-173")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[bravery_charm], active=[charmander]))
    starting_hp = charmander.hp

    actions = bravery_charm.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseToolAction)
    assert actions[0].target is charmander

    bravery_charm.reduce_action(actions[0], state)

    assert bravery_charm in charmander.attachment
    assert bravery_charm not in state.player1.hand
    assert bravery_charm.hasAttached is True
    assert bravery_charm.attachedTo == [charmander]
    assert charmander.hp == starting_hp + 50
    assert bravery_charm.get_actions(state) == []


def test_bravery_charm_is_unavailable_for_stage_one_pokemon():
    bravery_charm = make_card("PAL-173")
    charmeleon = make_card("PAF-008")
    state = make_state(PlayerZones(hand=[bravery_charm], active=[charmeleon]))

    assert bravery_charm.get_actions(state) == []


def test_bravery_charm_is_unavailable_when_basic_pokemon_already_has_tool():
    bravery_charm = make_card("PAL-173")
    charmander = make_card("PAF-007")
    charmander.attachment = [make_card("MEW-165")]
    state = make_state(PlayerZones(hand=[bravery_charm], active=[charmander]))

    assert bravery_charm.get_actions(state) == []
