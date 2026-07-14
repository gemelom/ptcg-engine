import pytest

from ptcg.core.action import AttackAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


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

    attacks = [a for a in charmeleon.get_actions(state) if isinstance(a, AttackAction) and a.attack.name == "Raging Flames"]
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

    attacks = [a for a in charmeleon.get_actions(state) if isinstance(a, AttackAction) and a.attack.name == "Slash"]
    assert len(attacks) == 1

    list(charmeleon.reduce_action(attacks[0], state))

    assert defender.hp == 50  # 70 - 20


def test_charmeleon_unavailable_without_energy():
    charmeleon = make_card("VIV-024")
    defender = make_card("PAF-007")
    state = make_state(PlayerZones(active=[charmeleon]), PlayerZones(active=[defender]))

    assert [a for a in charmeleon.get_actions(state) if isinstance(a, AttackAction)] == []
