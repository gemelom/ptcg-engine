import pytest

from ptcg.core.action import AttackAction, EvolvePokemonAction
from ptcg.core.enums import CardType, PlayerId
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAF-007")
@pytest.mark.card_coverage(
    "PAF-007",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_charmander_steady_firebreathing_deals_damage_when_energy_is_attached():
    charmander = make_card("PAF-007")
    target = make_card("PAF-007")
    charmander.energy = [CardType.FIRE, CardType.FIRE]
    state = make_state(
        PlayerZones(
            active=[charmander],
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-002")],
        ),
        PlayerZones(
            active=[target],
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-004")],
        ),
    )

    attacks = [
        action
        for action in charmander.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Steady Firebreathing"
    ]
    assert len(attacks) == 1

    drive_choices(charmander.reduce_action(attacks[0], state), [])

    assert target.hp == 40
    assert state.turn == PlayerId.PLAYER2


def test_charmander_has_no_attack_actions_without_energy():
    charmander = make_card("PAF-007")
    target = make_card("PAF-007")
    state = make_state(
        PlayerZones(active=[charmander]),
        PlayerZones(active=[target]),
    )

    assert charmander.get_actions(state) == []


@pytest.mark.card("PAF-008")
@pytest.mark.card_coverage(
    "PAF-008",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_charmeleon_combustion_deals_damage_when_energy_is_attached():
    charmeleon = make_card("PAF-008")
    target = make_card("PAF-007")
    charmeleon.energy = [CardType.FIRE, CardType.FIRE]
    state = make_state(
        PlayerZones(
            active=[charmeleon],
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-002")],
        ),
        PlayerZones(
            active=[target],
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-004")],
        ),
    )

    attacks = [
        action
        for action in charmeleon.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Combustion"
    ]
    assert len(attacks) == 1

    drive_choices(charmeleon.reduce_action(attacks[0], state), [])

    assert target.hp == 20
    assert state.turn == PlayerId.PLAYER2


def test_charmeleon_has_no_attack_actions_without_energy():
    charmeleon = make_card("PAF-008")
    target = make_card("PAF-007")
    state = make_state(
        PlayerZones(active=[charmeleon]),
        PlayerZones(active=[target]),
    )

    assert charmeleon.get_actions(state) == []


@pytest.mark.card("PAF-027")
@pytest.mark.card_coverage(
    "PAF-027",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_ralts_psyshot_deals_damage_with_psychic_and_colorless_energy():
    ralts = make_card("PAF-027")
    target = make_card("PAF-007")
    ralts.energy = [CardType.PSYCHIC, CardType.PSYCHIC]
    state = make_state(
        PlayerZones(
            active=[ralts],
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-002")],
        ),
        PlayerZones(
            active=[target],
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-004")],
        ),
    )

    attacks = [
        action
        for action in ralts.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Psyshot"
    ]
    assert len(attacks) == 1

    drive_choices(ralts.reduce_action(attacks[0], state), [])

    assert target.hp == 40
    assert state.turn == PlayerId.PLAYER2


def test_ralts_has_no_attack_actions_without_full_attack_cost():
    ralts = make_card("PAF-027")
    target = make_card("PAF-007")
    ralts.energy = [CardType.PSYCHIC]
    state = make_state(
        PlayerZones(active=[ralts]),
        PlayerZones(active=[target]),
    )

    assert ralts.get_actions(state) == []


@pytest.mark.card("PAF-054")
@pytest.mark.card_coverage(
    "PAF-054",
    "reduce_action",
    "choice_flow",
    "zone_change",
    "ability",
)
def test_charizard_ex_infernal_reign_attaches_selected_fire_energy_after_evolution():
    charizard_ex = make_card("PAF-054")
    charmander = make_card("PAF-007")
    fire_energy_1 = make_card("SVE-002")
    fire_energy_2 = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    state = make_state(
        PlayerZones(
            hand=[charizard_ex],
            active=[charmander],
            left=[fire_energy_1, fire_energy_2, lightning_energy],
        )
    )

    drive_choices(
        charizard_ex.reduce_action(
            EvolvePokemonAction(PlayerId.PLAYER1, charizard_ex, charmander),
            state,
        ),
        [
            lambda _info: [fire_energy_1, fire_energy_2],
            lambda _info: [charizard_ex],
            lambda _info: [charizard_ex],
        ],
    )

    assert state.player1.active == [charizard_ex]
    assert charmander in charizard_ex.evolved
    assert fire_energy_1 in charizard_ex.attachment
    assert fire_energy_2 in charizard_ex.attachment
    assert charizard_ex.energy == [CardType.FIRE, CardType.FIRE]
    assert lightning_energy in state.player1.left


@pytest.mark.card_coverage("PAF-054", "get_actions", "damage")
def test_charizard_ex_burning_darkness_adds_damage_for_opponent_taken_prizes():
    charizard_ex = make_card("PAF-054")
    target = make_card("PAF-054")
    charizard_ex.energy = [CardType.FIRE, CardType.FIRE]
    state = make_state(
        PlayerZones(
            active=[charizard_ex],
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-002")],
        ),
        PlayerZones(
            active=[target],
            left=[make_card("SVE-004")],
            prize=[
                make_card("SVE-004"),
                make_card("SVE-004"),
                make_card("SVE-004"),
                make_card("SVE-004"),
            ],
        ),
    )

    attacks = [
        action
        for action in charizard_ex.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Burning Darkness"
    ]
    assert len(attacks) == 1

    drive_choices(charizard_ex.reduce_action(attacks[0], state), [])

    assert target.hp == 90
    assert attacks[0].attack.damage == 240
