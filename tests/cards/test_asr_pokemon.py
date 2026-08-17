import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardPosition, CardType
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


def _attach_attack_energy(greninja):
    water_energy_1 = make_card("SVE-002")
    water_energy_1.provides = [CardType.WATER]
    water_energy_2 = make_card("SVE-005")
    water_energy_2.provides = [CardType.WATER]
    colorless_energy = make_card("TEF-161")
    attached = [water_energy_1, water_energy_2, colorless_energy]
    for index, energy in enumerate(attached, start=1):
        energy.cardPosition = CardPosition.ACTIVE_ATTACHMENT
        energy.index = index
    greninja.attachment = attached
    greninja.energy = [CardType.WATER, CardType.WATER, CardType.COLORLESS]
    return list(attached)


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

    drive_choices(
        greninja.reduce_action(ability_actions[0], state),
        [lambda _info: [fire_energy]],
    )

    assert fire_energy in state.player1.discard
    assert state.player1.hand == drawn_cards
    assert state.player1.left == []
    assert greninja.abilityUsed is True
    assert state.player1.onceUsedTurn["Concealed Cards"] is True


def test_radiant_greninja_concealed_cards_unavailable_without_energy():
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


def test_radiant_greninja_concealed_cards_allows_energy_choice():
    greninja = make_card("ASR-046")
    fire_energy = make_card("SVE-002")
    mist_energy = make_card("TEF-161")
    state = make_state(
        PlayerZones(
            hand=[fire_energy, mist_energy],
            left=[make_card("PAF-007"), make_card("PAF-008")],
            active=[greninja],
        )
    )
    state.player1.onceUsedTurn["Concealed Cards"] = False
    ability = next(
        action for action in greninja.get_actions(state) if isinstance(action, UseAbilityAction)
    )

    drive_choices(
        greninja.reduce_action(ability, state),
        [lambda _info: [mist_energy]],
    )

    assert mist_energy in state.player1.discard
    assert fire_energy in state.player1.hand


def test_radiant_greninja_moonlight_shuriken_uses_chosen_energy_and_targets():
    greninja = make_card("ASR-046")
    attached_energy = _attach_attack_energy(greninja)
    defending_active = make_card("PAF-054")
    defending_active.weakness = [CardType.WATER]
    unselected_bench = make_card("PAF-054")
    selected_bench = make_card("PAF-054")
    selected_bench.weakness = [CardType.WATER]
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
            bench=[unselected_bench, selected_bench],
        ),
    )
    state.player1.onceUsedTurn["Concealed Cards"] = False

    actions = greninja.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1
    assert attack_actions[0].target is defending_active

    drive_choices(
        greninja.reduce_action(attack_actions[0], state),
        [
            lambda _info: attached_energy[:2],
            lambda _info: [defending_active, selected_bench],
        ],
    )

    assert defending_active.hp == 150  # Weakness applies to the Active Pokémon.
    assert selected_bench.hp == 240  # Weakness is not applied on the Bench.
    assert unselected_bench.hp == 330
    assert greninja.energy == [CardType.COLORLESS]
    assert greninja.attachment == [attached_energy[2]]
    assert state.player1.discard == attached_energy[:2]
    assert state.turn == state.player2.id
    assert greninja.cardPosition == CardPosition.ACTIVE


def test_radiant_greninja_moonlight_shuriken_handles_knockout_and_prize():
    greninja = make_card("ASR-046")
    attached_energy = _attach_attack_energy(greninja)
    defending_active = make_card("PAF-054")
    defending_bench = make_card("PAF-007")
    prizes = [make_card("SVE-004"), make_card("SVE-005")]
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-008")],
            prize=prizes,
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
    attack = next(
        action for action in greninja.get_actions(state) if isinstance(action, AttackAction)
    )

    drive_choices(
        greninja.reduce_action(attack, state),
        [
            lambda _info: attached_energy[:2],
            lambda _info: [defending_active, defending_bench],
            lambda info: [info["prompt"].candidates[0]],
        ],
    )

    assert defending_bench not in state.player2.bench
    assert any(card.name == defending_bench.name for card in state.player2.discard)
    assert len(state.player1.prize) == 1
    assert len(state.player1.hand) == 1
