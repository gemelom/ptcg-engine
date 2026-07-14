import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SVI-086")
@pytest.mark.card_coverage(
    "SVI-086",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_gardevoir_ex_miracle_force_damages_opponent():
    gardevoir = make_card("SVI-086")
    gardevoir.energy = [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[gardevoir],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    attacks = [a for a in gardevoir.get_actions(state) if isinstance(a, AttackAction)]
    assert len(attacks) == 1
    assert attacks[0].attack.name == "Miracle Force"

    list(gardevoir.reduce_action(attacks[0], state))

    assert defender.hp == 140  # 330 - 190
    assert state.turn == state.player2.id


def test_gardevoir_ex_miracle_force_unavailable_without_energy():
    gardevoir = make_card("SVI-086")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[gardevoir]), PlayerZones(active=[defender]))

    assert [a for a in gardevoir.get_actions(state) if isinstance(a, AttackAction)] == []


def test_gardevoir_ex_miracle_force_unavailable_when_on_bench():
    gardevoir = make_card("SVI-086")
    gardevoir.energy = [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS]
    active = make_card("PAF-007")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(active=[active], bench=[gardevoir]),
        PlayerZones(active=[defender]),
    )

    assert [a for a in gardevoir.get_actions(state) if isinstance(a, AttackAction)] == []


@pytest.mark.card("SVI-253")
@pytest.mark.card_coverage(
    "SVI-253",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "damage",
    "ability",
)
def test_miraidon_ex_tandem_unit_puts_lightning_pokemon_on_bench():
    miraidon = make_card("SVI-253")
    lightning1 = make_card("SVI-253")   # another Miraidon ex - Basic Lightning
    lightning2 = make_card("BRS-048")   # Raikou V - Basic Lightning
    non_lightning = make_card("PAF-007")
    state = make_state(
        PlayerZones(
            left=[lightning1, lightning2, non_lightning],
            active=[miraidon],
        )
    )
    state.player1.onceUsedTurn["Tandem Unit"] = False

    ability_actions = [a for a in miraidon.get_actions(state) if isinstance(a, UseAbilityAction)]
    assert len(ability_actions) == 1

    prompts = drive_choices(
        miraidon.reduce_action(ability_actions[0], state),
        [lambda _info: [lightning1, lightning2]],
    )

    assert prompts[0]["prompt"].source is miraidon
    assert set(prompts[0]["prompt"].candidates) == {lightning1, lightning2}
    assert len(state.player1.bench) == 2
    assert miraidon.abilityUsed is True
    assert state.player1.onceUsedTurn["Tandem Unit"] is True


def test_miraidon_ex_tandem_unit_unavailable_after_use():
    miraidon = make_card("SVI-253")
    state = make_state(PlayerZones(left=[make_card("BRS-048")], active=[miraidon]))
    state.player1.onceUsedTurn["Tandem Unit"] = True

    assert [a for a in miraidon.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_miraidon_ex_photon_blaster_damages_opponent():
    miraidon = make_card("SVI-253")
    miraidon.energy = [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[miraidon],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Tandem Unit"] = False

    attacks = [a for a in miraidon.get_actions(state) if isinstance(a, AttackAction)]
    assert len(attacks) == 1

    list(miraidon.reduce_action(attacks[0], state))

    assert defender.hp == 110  # 330 - 220
    assert state.turn == state.player2.id


def test_miraidon_ex_photon_blaster_unavailable_after_use():
    miraidon = make_card("SVI-253")
    miraidon.energy = [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS]
    miraidon.useAttackLastTurn = True
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[miraidon]), PlayerZones(active=[defender]))
    state.player1.onceUsedTurn["Tandem Unit"] = False

    assert [a for a in miraidon.get_actions(state) if isinstance(a, AttackAction)] == []
