import pytest

from ptcg.core.action import AttackAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PGO-029")
@pytest.mark.card_coverage(
    "PGO-029",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
    "ability",
)
def test_zapdos_lightning_symbol_adds_damage_to_basic_lightning_non_zapdos_attack():
    zapdos = make_card("PGO-029")
    attacker = make_card("BRS-048")
    attacker.energy = [CardType.LIGHTNING, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(active=[attacker], bench=[zapdos]),
        PlayerZones(active=[defender]),
    )
    action = AttackAction(state.player1.id, attacker, attacker.attacks[0], defender)
    action.attack.damage = 80

    zapdos.use_ability(action, state)

    assert action.attack.damage == 90


def test_zapdos_lightning_symbol_does_not_add_damage_to_zapdos_attack():
    zapdos = make_card("PGO-029")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[zapdos]), PlayerZones(active=[defender]))
    action = AttackAction(state.player1.id, zapdos, zapdos.attacks[0], defender)
    action.attack.damage = 110

    zapdos.use_ability(action, state)

    assert action.attack.damage == 110


def test_zapdos_electric_ball_damages_opponents_active_pokemon():
    zapdos = make_card("PGO-029")
    zapdos.energy = [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[zapdos],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    electric_ball = [
        action
        for action in zapdos.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Electric Ball"
    ]
    assert len(electric_ball) == 1

    list(zapdos.reduce_action(electric_ball[0], state))

    assert defender.hp == 220
    assert state.turn == state.player2.id


def test_zapdos_electric_ball_unavailable_without_energy():
    zapdos = make_card("PGO-029")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[zapdos]), PlayerZones(active=[defender]))

    assert [
        action for action in zapdos.get_actions(state) if isinstance(action, AttackAction)
    ] == []
