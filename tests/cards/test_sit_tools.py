import pytest

from ptcg.core.action import UseAbilityAction, UseToolAction
from ptcg.core.enums import CardTag
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SIT-156")
@pytest.mark.card_coverage(
    "SIT-156",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "ability",
)
def test_forest_seal_stone_attaches_to_pokemon_v():
    stone = make_card("SIT-156")
    lugia_v = make_card("SIT-138")  # Lugia V - Pokemon V
    state = make_state(PlayerZones(hand=[stone], active=[lugia_v]))

    actions = stone.get_actions(state)
    tool_actions = [a for a in actions if isinstance(a, UseToolAction)]
    assert len(tool_actions) == 1
    assert tool_actions[0].target is lugia_v

    list(stone.reduce_action(tool_actions[0], state))

    assert stone.hasAttached is True
    assert stone.attachedTo == [lugia_v]
    assert stone not in state.player1.hand


def test_forest_seal_stone_star_alchemy_searches_any_card():
    stone = make_card("SIT-156")
    lugia_v = make_card("SIT-138")
    target_card = make_card("PAF-084")
    other_card = make_card("SVE-002")
    stone.hasAttached = True
    stone.attachedTo = [lugia_v]
    state = make_state(PlayerZones(left=[target_card, other_card], active=[lugia_v]))
    state.player1.onceUsedGame[CardTag.VSTAR] = False

    ability_actions = [a for a in stone.get_actions(state) if isinstance(a, UseAbilityAction)]
    assert len(ability_actions) == 1

    prompts = drive_choices(
        stone.reduce_action(ability_actions[0], state),
        [lambda _info: [target_card]],
    )

    assert prompts[0]["prompt"].source is stone
    assert target_card in state.player1.hand
    assert state.player1.onceUsedGame[CardTag.VSTAR] is True


def test_forest_seal_stone_star_alchemy_unavailable_when_vstar_used():
    stone = make_card("SIT-156")
    lugia_v = make_card("SIT-138")
    stone.hasAttached = True
    stone.attachedTo = [lugia_v]
    state = make_state(PlayerZones(left=[make_card("SVE-002")], active=[lugia_v]))
    state.player1.onceUsedGame[CardTag.VSTAR] = True

    assert [a for a in stone.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_forest_seal_stone_star_alchemy_unavailable_on_non_v_pokemon():
    stone = make_card("SIT-156")
    charmander = make_card("PAF-007")  # Basic, not V
    stone.hasAttached = True
    stone.attachedTo = [charmander]
    state = make_state(PlayerZones(left=[make_card("SVE-002")], active=[charmander]))
    state.player1.onceUsedGame[CardTag.VSTAR] = False

    assert [a for a in stone.get_actions(state) if isinstance(a, UseAbilityAction)] == []
