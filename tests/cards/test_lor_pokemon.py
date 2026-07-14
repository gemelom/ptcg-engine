import pytest

from ptcg.core.action import AttackAction, EffectAction
from ptcg.core.effect import Effect
from ptcg.core.enums import CardType, SpecialCondition
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("LOR-143")
@pytest.mark.card_coverage(
    "LOR-143",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
    "ability",
)
def test_snorlax_thumping_snore_damages_target_then_becomes_asleep():
    snorlax = make_card("LOR-143")
    snorlax.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[snorlax],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    actions = snorlax.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1

    list(snorlax.reduce_action(attack_actions[0], state))

    assert defender.hp == 150
    assert snorlax.specialCondition == SpecialCondition.ASLEEP
    assert state.turn == state.player2.id


def test_snorlax_thumping_snore_unavailable_without_three_energy():
    snorlax = make_card("LOR-143")
    snorlax.energy = [CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[snorlax]), PlayerZones(active=[defender]))

    assert [action for action in snorlax.get_actions(state) if isinstance(action, AttackAction)] == []


def test_snorlax_unfazed_fat_prevents_effects_but_not_damage():
    snorlax = make_card("LOR-143")
    attacker = make_card("PRE-043")
    effect = Effect(dc=3, specialCondition=SpecialCondition.ASLEEP)
    state = make_state(PlayerZones(active=[snorlax]))
    action = EffectAction(state.player1.id, attacker, effect, snorlax)

    snorlax.use_ability(action, state)

    assert effect.dc == 0
    assert effect.specialCondition is None
