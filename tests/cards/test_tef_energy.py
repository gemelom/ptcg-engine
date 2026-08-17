import pytest

from ptcg.core.action import AttachEnergyAction, AttackAction, EffectAction
from ptcg.core.effect import Effect
from ptcg.core.enums import CardType, SpecialCondition
from ptcg.core.reducer import reduce_attack_action, reduce_effect_action
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
def test_mist_energy_attaches_as_colorless_energy():
    mist_energy = make_card("TEF-161")
    charmander = make_card("PAF-007")
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


def test_mist_energy_prevents_attack_effects_but_not_damage():
    attacker = make_card("PAF-007")
    target = make_card("PAF-027")
    mist_energy = make_card("TEF-161")
    target.attachment.append(mist_energy)
    target.energy.extend(mist_energy.provides)
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[attacker],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[target],
        ),
    )

    attack = attacker.attacks[0]
    hp_before_attack = target.hp
    list(
        reduce_attack_action(
            AttackAction(state.turn, attacker, attack, target),
            state,
            auto_end_turn=False,
        )
    )

    assert target.hp == hp_before_attack - attack.damage

    effect = Effect(dc=3, specialCondition=SpecialCondition.ASLEEP)
    hp_before_effect = target.hp
    list(
        reduce_effect_action(
            EffectAction(state.turn, attacker, effect, target),
            state,
        )
    )

    assert target.hp == hp_before_effect
    assert effect.dc == 0
    assert effect.specialCondition is None

    target.attachment.remove(mist_energy)
    attacker.attachment.append(mist_energy)
    own_effect = Effect(dc=1)
    hp_before_own_effect = attacker.hp
    list(
        reduce_effect_action(
            EffectAction(state.turn, attacker, own_effect, attacker),
            state,
        )
    )

    assert attacker.hp == hp_before_own_effect - 10
