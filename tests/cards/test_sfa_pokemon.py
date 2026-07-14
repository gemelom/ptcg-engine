import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SFA-092")
@pytest.mark.card_coverage(
    "SFA-092",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_fezandipiti_ex_flip_the_script_draws_three_after_pokemon_was_knocked_out():
    fezandipiti = make_card("SFA-092")
    drawn_cards = [make_card("SVE-002"), make_card("SVE-004"), make_card("SVE-005")]
    remaining_card = make_card("SVE-007")
    state = make_state(PlayerZones(left=drawn_cards + [remaining_card], bench=[fezandipiti]))
    state.player1.hasPokemonDead = True
    state.player1.onceUsedTurn["Flip the Script"] = False

    actions = fezandipiti.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    list(fezandipiti.reduce_action(ability_actions[0], state))

    assert state.player1.hand == drawn_cards
    assert state.player1.left == [remaining_card]
    assert fezandipiti.abilityUsed is True
    assert state.player1.onceUsedTurn["Flip the Script"] is True


def test_fezandipiti_ex_flip_the_script_unavailable_without_knockout_last_turn():
    fezandipiti = make_card("SFA-092")
    state = make_state(PlayerZones(bench=[fezandipiti]))
    state.player1.hasPokemonDead = False
    state.player1.onceUsedTurn["Flip the Script"] = False

    assert [
        action for action in fezandipiti.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_fezandipiti_ex_cruel_arrow_places_ten_damage_counters_on_chosen_pokemon():
    fezandipiti = make_card("SFA-092")
    fezandipiti.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    opponent_active = make_card("PAF-054")
    chosen_bench = make_card("PAF-054")
    other_bench = make_card("PAF-027")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[fezandipiti],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[opponent_active],
            bench=[chosen_bench, other_bench],
        ),
    )
    state.player1.onceUsedTurn["Flip the Script"] = False

    cruel_arrow = [
        action
        for action in fezandipiti.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Cruel Arrow"
    ]
    assert len(cruel_arrow) == 1

    prompts = drive_choices(
        fezandipiti.reduce_action(cruel_arrow[0], state),
        [lambda _info: [chosen_bench]],
    )

    assert prompts[0]["prompt"].source is fezandipiti
    assert prompts[0]["prompt"].candidates == [opponent_active, chosen_bench, other_bench]
    assert opponent_active.hp == 330
    assert chosen_bench.hp == 230
    assert other_bench.hp == 70
    assert state.turn == state.player2.id


def test_fezandipiti_ex_cruel_arrow_unavailable_without_energy():
    fezandipiti = make_card("SFA-092")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[fezandipiti]), PlayerZones(active=[defender]))

    assert [
        action for action in fezandipiti.get_actions(state) if isinstance(action, AttackAction)
    ] == []
