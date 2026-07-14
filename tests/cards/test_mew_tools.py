import pytest

from ptcg.core.action import AttackAction, UseToolAction
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("MEW-165")
@pytest.mark.card_coverage(
    "MEW-165",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
    "ability",
)
def test_rigid_band_attaches_to_pokemon_without_tool():
    rigid_band = make_card("MEW-165")
    pidgeotto = make_card("MEW-017")
    state = make_state(PlayerZones(hand=[rigid_band], active=[pidgeotto]))

    actions = rigid_band.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseToolAction)
    assert actions[0].target is pidgeotto

    rigid_band.reduce_action(actions[0], state)

    assert rigid_band in pidgeotto.attachment
    assert rigid_band not in state.player1.hand
    assert rigid_band.hasAttached is True
    assert rigid_band.attachedTo == [pidgeotto]
    assert rigid_band.get_actions(state) == []


def test_rigid_band_reduces_attack_damage_to_stage_one_holder():
    rigid_band = make_card("MEW-165")
    pidgeotto = make_card("MEW-017")
    rigid_band.attachedTo = [pidgeotto]
    attacker = make_card("MEW-123")
    action = AttackAction(make_state().player1.id, attacker, attacker.attacks[1], pidgeotto)
    action.attack.damage = 70

    rigid_band.use_ability(action, make_state())

    assert action.attack.damage == 40


def test_rigid_band_does_not_reduce_damage_to_basic_holder():
    rigid_band = make_card("MEW-165")
    pidgey = make_card("MEW-016")
    rigid_band.attachedTo = [pidgey]
    attacker = make_card("MEW-123")
    action = AttackAction(make_state().player1.id, attacker, attacker.attacks[1], pidgey)
    action.attack.damage = 70

    rigid_band.use_ability(action, make_state())

    assert action.attack.damage == 70
