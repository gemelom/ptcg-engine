import pytest

from ptcg.core.action import UseSupporterAction
from ptcg.core.enums import PokemonPosition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAR-257")
@pytest.mark.card_coverage(
    "PAR-257",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_professor_turos_scenario_returns_benched_pokemon_to_hand_and_discards_attachment():
    professor_turo = make_card("PAR-257")
    active = make_card("PAF-054")
    benched = make_card("PAF-007")
    attached_tool = make_card("PAL-173")
    benched.attachment = [attached_tool]
    state = make_state(PlayerZones(hand=[professor_turo], active=[active], bench=[benched]))

    actions = professor_turo.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseSupporterAction)

    prompts = drive_choices(
        professor_turo.reduce_action(actions[0], state),
        [lambda _info: [benched]],
    )

    assert prompts[0]["prompt"].source is professor_turo
    assert prompts[0]["prompt"].candidates == [active, benched]
    assert state.player1.active == [active]
    assert state.player1.bench == []
    assert [card.name for card in state.player1.hand] == ["Charmander"]
    assert [card.name for card in state.player1.discard] == [
        "Professor Turo's Scenario",
        "Bravery Charm",
    ]
    assert state.player1.supporterPlayedTurn is True


def test_professor_turos_scenario_returns_active_pokemon_and_promotes_chosen_bench():
    professor_turo = make_card("PAR-257")
    active = make_card("PAF-054")
    replacement = make_card("PAF-007")
    other_bench = make_card("PAF-027")
    state = make_state(
        PlayerZones(
            hand=[professor_turo],
            active=[active],
            bench=[replacement, other_bench],
        )
    )

    prompts = drive_choices(
        professor_turo.reduce_action(professor_turo.get_actions(state)[0], state),
        [
            lambda _info: [active],
            lambda _info: [replacement],
        ],
    )

    assert prompts[0]["prompt"].candidates == [active, replacement, other_bench]
    assert prompts[1]["prompt"].candidates == [replacement, other_bench]
    assert state.player1.active == [replacement]
    assert state.player1.bench == [other_bench]
    assert replacement.position == PokemonPosition.ACTIVE
    assert [card.name for card in state.player1.hand] == ["Charizard ex"]
    assert state.player1.discard == [professor_turo]


def test_professor_turos_scenario_is_unavailable_with_only_one_pokemon_in_play():
    professor_turo = make_card("PAR-257")
    state = make_state(PlayerZones(hand=[professor_turo], active=[make_card("PAF-054")]))

    assert professor_turo.get_actions(state) == []


def test_professor_turos_scenario_is_unavailable_after_supporter_played():
    professor_turo = make_card("PAR-257")
    state = make_state(
        PlayerZones(
            hand=[professor_turo],
            active=[make_card("PAF-054")],
            bench=[make_card("PAF-007")],
        )
    )
    state.player1.supporterPlayedTurn = True

    assert professor_turo.get_actions(state) == []
