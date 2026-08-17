import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("VIV-025")
@pytest.mark.card_coverage(
    "VIV-025",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "damage",
    "ability",
    "zone_change",
)
def test_charizard_battle_sense_keeps_one_of_top_three_and_discards_others():
    charizard = make_card("VIV-025")
    first = make_card("SVE-002")
    chosen = make_card("SVE-004")
    third = make_card("SVE-005")
    fourth = make_card("SVE-007")
    state = make_state(PlayerZones(left=[first, chosen, third, fourth], active=[charizard]))

    action = next(
        action for action in charizard.get_actions(state) if isinstance(action, UseAbilityAction)
    )
    prompts = drive_choices(
        charizard.reduce_action(action, state),
        [lambda _info: [chosen]],
    )

    assert prompts[0]["prompt"].source is charizard
    assert prompts[0]["prompt"].candidates == [first, chosen, third]
    assert state.player1.hand == [chosen]
    assert state.player1.discard == [first, third]
    assert state.player1.left == [fourth]
    assert charizard.abilityUsed is True
    assert [
        action for action in charizard.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_charizard_battle_sense_handles_a_one_card_deck():
    charizard = make_card("VIV-025")
    only_card = make_card("SVE-002")
    state = make_state(PlayerZones(left=[only_card], bench=[charizard]))
    action = next(
        action for action in charizard.get_actions(state) if isinstance(action, UseAbilityAction)
    )

    drive_choices(charizard.reduce_action(action, state), [lambda _info: [only_card]])

    assert state.player1.hand == [only_card]
    assert state.player1.left == []
    assert state.player1.discard == []


def test_charizard_battle_sense_unavailable_with_an_empty_deck():
    charizard = make_card("VIV-025")
    state = make_state(PlayerZones(active=[charizard]))

    assert [
        action for action in charizard.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_charizard_royal_blaze_adds_damage_for_each_leon_in_discard():
    charizard = make_card("VIV-025")
    charizard.energy = [CardType.FIRE, CardType.FIRE]
    first_leon = make_card("SVE-002")
    first_leon.name = "Leon"
    second_leon = make_card("SVE-004")
    second_leon.name = "Leon"
    non_leon = make_card("SVE-005")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-007")],
            discard=[first_leon, non_leon, second_leon],
            prize=[make_card("SVE-008")],
            active=[charizard],
        ),
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[defender],
        ),
    )

    action = next(
        action
        for action in charizard.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Royal Blaze"
    )
    list(charizard.reduce_action(action, state))

    assert defender.hp == 130  # 330 - (100 + 2 * 50)
    assert charizard.attacks[0].damage == 100
    assert state.turn == state.player2.id


def test_charizard_royal_blaze_unavailable_without_energy_or_from_bench():
    charizard = make_card("VIV-025")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[charizard]), PlayerZones(active=[defender]))

    assert [
        action for action in charizard.get_actions(state) if isinstance(action, AttackAction)
    ] == []

    charizard.energy = [CardType.FIRE, CardType.FIRE]
    state = make_state(
        PlayerZones(active=[make_card("PAF-007")], bench=[charizard]),
        PlayerZones(active=[defender]),
    )

    assert [
        action for action in charizard.get_actions(state) if isinstance(action, AttackAction)
    ] == []


@pytest.mark.card("VIV-024")
@pytest.mark.card_coverage(
    "VIV-024",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
    "zone_change",
)
def test_charmeleon_raging_flames_damages_and_discards_top_three():
    charmeleon = make_card("VIV-024")
    charmeleon.energy = [CardType.FIRE, CardType.FIRE]
    deck_cards = [make_card("SVE-002"), make_card("SVE-004"), make_card("SVE-005")]
    defender = make_card("PAF-007")
    state = make_state(
        PlayerZones(left=deck_cards, prize=[make_card("SVE-007")], active=[charmeleon]),
        PlayerZones(left=[make_card("SVE-008")], prize=[make_card("SVE-007")], active=[defender]),
    )

    attacks = [
        a
        for a in charmeleon.get_actions(state)
        if isinstance(a, AttackAction) and a.attack.name == "Raging Flames"
    ]
    assert len(attacks) == 1

    list(charmeleon.reduce_action(attacks[0], state))

    assert defender.hp == 10  # 70 - 60
    assert len(state.player1.left) == 0
    assert all(c in state.player1.discard for c in deck_cards)
    assert state.turn == state.player2.id


def test_charmeleon_slash_damages_opponent():
    charmeleon = make_card("VIV-024")
    charmeleon.energy = [CardType.FIRE]
    defender = make_card("PAF-007")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], prize=[make_card("SVE-004")], active=[charmeleon]),
        PlayerZones(left=[make_card("SVE-005")], prize=[make_card("SVE-007")], active=[defender]),
    )

    attacks = [
        a
        for a in charmeleon.get_actions(state)
        if isinstance(a, AttackAction) and a.attack.name == "Slash"
    ]
    assert len(attacks) == 1

    list(charmeleon.reduce_action(attacks[0], state))

    assert defender.hp == 50  # 70 - 20


def test_charmeleon_unavailable_without_energy():
    charmeleon = make_card("VIV-024")
    defender = make_card("PAF-007")
    state = make_state(PlayerZones(active=[charmeleon]), PlayerZones(active=[defender]))

    assert [a for a in charmeleon.get_actions(state) if isinstance(a, AttackAction)] == []
