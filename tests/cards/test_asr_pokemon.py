import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardPosition, CardType
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("ASR-046")
@pytest.mark.card_coverage(
    "ASR-046",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_radiant_greninja_concealed_cards_discards_energy_and_draws_two():
    greninja = make_card("ASR-046")
    fire_energy = make_card("SVE-002")
    drawn_cards = [make_card("PAF-007"), make_card("PAF-008")]
    state = make_state(
        PlayerZones(
            hand=[fire_energy],
            left=drawn_cards,
            active=[greninja],
        )
    )
    state.player1.onceUsedTurn["Concealed Cards"] = False

    actions = greninja.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    list(greninja.reduce_action(ability_actions[0], state))

    assert fire_energy in state.player1.discard
    assert state.player1.hand == drawn_cards
    assert state.player1.left == []
    assert greninja.abilityUsed is True
    assert state.player1.onceUsedTurn["Concealed Cards"] is True


def test_radiant_greninja_concealed_cards_unavailable_without_basic_energy():
    greninja = make_card("ASR-046")
    state = make_state(
        PlayerZones(
            hand=[make_card("PAF-084")],
            active=[greninja],
        )
    )
    state.player1.onceUsedTurn["Concealed Cards"] = False

    assert [
        action for action in greninja.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_radiant_greninja_moonlight_shuriken_damages_two_opposing_pokemon():
    greninja = make_card("ASR-046")
    greninja.energy = [CardType.WATER, CardType.WATER, CardType.COLORLESS]
    defending_active = make_card("PAF-054")
    defending_bench = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-005")],
            active=[greninja],
        ),
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-007")],
            active=[defending_active],
            bench=[defending_bench],
        ),
    )
    state.player1.onceUsedTurn["Concealed Cards"] = False

    actions = greninja.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1
    assert attack_actions[0].target is defending_active

    list(greninja.reduce_action(attack_actions[0], state))

    assert defending_active.hp == 240
    assert defending_bench.hp == 240
    assert greninja.energy == [CardType.COLORLESS]
    assert state.turn == state.player2.id
    assert greninja.cardPosition == CardPosition.ACTIVE
