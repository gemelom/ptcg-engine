import pytest

from ptcg.core.action import AttachEnergyAction, AttackAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("TEF-161")
@pytest.mark.card_coverage(
    "TEF-161",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
    "ability",
)
def test_mist_energy_attaches_as_colorless_and_blocks_effect_attack_damage():
    mist_energy = make_card("TEF-161")
    charmander = make_card("PAF-007")
    target = make_card("PAF-027")
    state = make_state(PlayerZones(hand=[mist_energy], active=[charmander]))

    actions = mist_energy.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], AttachEnergyAction)
    assert actions[0].target is charmander

    mist_energy.reduce_action(actions[0], state)

    assert mist_energy in charmander.attachment
    assert CardType.COLORLESS in charmander.energy
    assert state.player1.energyPlayedTurn is True
    assert mist_energy.get_actions(state) == []

    attack = charmander.attacks[1]
    attack.damage = 50
    attack.effectAttack = True
    action = AttackAction(state.turn, charmander, attack, target)

    mist_energy.use_ability(action, state)

    assert attack.damage == 0
