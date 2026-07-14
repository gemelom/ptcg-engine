import pytest

from ptcg.core.action import UseItemAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SFA-061")
@pytest.mark.card_coverage(
    "SFA-061",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_night_stretcher_moves_selected_pokemon_from_discard_to_hand():
    night_stretcher = make_card("SFA-061")
    pokemon = make_card("PAF-007")
    basic_energy = make_card("SVE-002")
    non_candidate = make_card("PAF-084")
    state = make_state(
        PlayerZones(
            hand=[night_stretcher],
            discard=[pokemon, non_candidate, basic_energy],
        )
    )

    actions = night_stretcher.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        night_stretcher.reduce_action(actions[0], state),
        [lambda _info: [pokemon]],
    )

    assert prompts[0]["prompt"].source is night_stretcher
    assert prompts[0]["prompt"].candidates == [pokemon, basic_energy]
    assert state.player1.hand == [pokemon]
    assert night_stretcher in state.player1.discard
    assert non_candidate in state.player1.discard
    assert basic_energy in state.player1.discard


def test_night_stretcher_moves_selected_basic_energy_from_discard_to_hand():
    night_stretcher = make_card("SFA-061")
    basic_energy = make_card("SVE-002")
    state = make_state(PlayerZones(hand=[night_stretcher], discard=[basic_energy]))

    prompts = drive_choices(
        night_stretcher.reduce_action(night_stretcher.get_actions(state)[0], state),
        [lambda _info: [basic_energy]],
    )

    assert prompts[0]["prompt"].candidates == [basic_energy]
    assert state.player1.hand == [basic_energy]
    assert state.player1.discard == [night_stretcher]


def test_night_stretcher_is_unavailable_without_pokemon_or_basic_energy_in_discard():
    night_stretcher = make_card("SFA-061")
    state = make_state(PlayerZones(hand=[night_stretcher], discard=[make_card("PAF-084")]))

    assert night_stretcher.get_actions(state) == []
