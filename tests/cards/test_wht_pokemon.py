import pytest

from ptcg.core.action import AttackAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("WHT-044")
@pytest.mark.card_coverage(
    "WHT-044",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_frillish_slap_damages_opponent():
    frillish = make_card("WHT-044")
    frillish.energy = [CardType.PSYCHIC, CardType.COLORLESS]
    defender = make_card("PAF-007")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], prize=[make_card("SVE-004")], active=[frillish]),
        PlayerZones(left=[make_card("SVE-005")], prize=[make_card("SVE-007")], active=[defender]),
    )

    attacks = [a for a in frillish.get_actions(state) if isinstance(a, AttackAction) and a.attack.name == "Slap"]
    assert len(attacks) == 1

    list(frillish.reduce_action(attacks[0], state))

    assert defender.hp == 30  # 70 - 40
    assert state.turn == state.player2.id


def test_frillish_oceanic_gloom_damages_opponent():
    frillish = make_card("WHT-044")
    frillish.energy = [CardType.PSYCHIC]
    defender = make_card("PAF-007")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], prize=[make_card("SVE-004")], active=[frillish]),
        PlayerZones(left=[make_card("SVE-005")], prize=[make_card("SVE-007")], active=[defender]),
    )

    attacks = [a for a in frillish.get_actions(state) if isinstance(a, AttackAction) and a.attack.name == "Oceanic Gloom"]
    assert len(attacks) == 1

    list(frillish.reduce_action(attacks[0], state))

    assert defender.hp == 50  # 70 - 20


def test_frillish_unavailable_without_energy():
    frillish = make_card("WHT-044")
    defender = make_card("PAF-007")
    state = make_state(PlayerZones(active=[frillish]), PlayerZones(active=[defender]))

    assert [a for a in frillish.get_actions(state) if isinstance(a, AttackAction)] == []
