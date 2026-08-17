from __future__ import annotations

from ptcg.core.action import AttackAction
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


def test_attack_action_has_an_isolated_runtime_attack_context():
    attacker = make_card("PAF-007")
    defender = make_card("PAF-054")
    attack_template = attacker.attacks[0]
    first = AttackAction(make_state().player1.id, attacker, attack_template, defender)
    second = AttackAction(make_state().player1.id, attacker, attack_template, defender)

    first.attack.damage = 999

    assert first.attack_template is attack_template
    assert first.attack is not attack_template
    assert second.attack.damage == attack_template.damage
    assert attacker.attacks[0].damage != 999


def test_passive_damage_modifier_does_not_mutate_future_attacks():
    attacker = make_card("ASR-046")
    manaphy = make_card("BRS-041")
    defender = make_card("PAF-007")
    state = make_state(
        PlayerZones(active=[attacker]),
        PlayerZones(active=[manaphy], bench=[defender]),
    )
    attack_template = attacker.attacks[0]
    attack_template.damage = 90
    protected_action = AttackAction(state.player1.id, attacker, attack_template, defender)

    manaphy.use_ability(protected_action, state)
    future_action = AttackAction(state.player1.id, attacker, attack_template, defender)

    assert protected_action.attack.damage == 0
    assert future_action.attack.damage == 90
    assert attack_template.damage == 90
