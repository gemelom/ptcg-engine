import pytest

from ptcg.core.action import UseItemAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("OBF-189")
@pytest.mark.card_coverage(
    "OBF-189",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_letter_of_encouragement_searches_three_basic_energy_after_knockout(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    letter = make_card("OBF-189")
    fire_energy = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    psychic_energy = make_card("SVE-005")
    fourth_energy = make_card("SVE-007")
    pokemon = make_card("PAF-007")
    state = make_state(
        PlayerZones(
            hand=[letter],
            left=[fire_energy, pokemon, lightning_energy, psychic_energy, fourth_energy],
        )
    )
    state.player1.hasPokemonDead = True

    actions = letter.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        letter.reduce_action(actions[0], state),
        [lambda _info: [fire_energy, lightning_energy, psychic_energy]],
    )

    assert prompts[0]["prompt"].source is letter
    assert prompts[0]["prompt"].candidates == [
        fire_energy,
        lightning_energy,
        psychic_energy,
        fourth_energy,
    ]
    assert state.player1.hand == [fire_energy, lightning_energy, psychic_energy]
    assert state.player1.left == [pokemon, fourth_energy]
    assert state.player1.discard == [letter]


def test_letter_of_encouragement_can_choose_no_energy_after_knockout(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    letter = make_card("OBF-189")
    fire_energy = make_card("SVE-002")
    pokemon = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[letter], left=[fire_energy, pokemon]))
    state.player1.hasPokemonDead = True

    prompts = drive_choices(
        letter.reduce_action(letter.get_actions(state)[0], state),
        [lambda _info: []],
    )

    assert prompts[0]["prompt"].candidates == [fire_energy]
    assert state.player1.hand == []
    assert state.player1.left == [fire_energy, pokemon]
    assert state.player1.discard == [letter]


def test_letter_of_encouragement_is_unavailable_without_previous_knockout():
    letter = make_card("OBF-189")
    state = make_state(PlayerZones(hand=[letter], left=[make_card("SVE-002")]))

    assert letter.get_actions(state) == []
