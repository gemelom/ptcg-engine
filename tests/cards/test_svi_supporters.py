import pytest

from ptcg.core.action import UseSupporterAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SVI-175")
@pytest.mark.card_coverage(
    "SVI-175",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_jacq_searches_up_to_two_evolution_pokemon():
    jacq = make_card("SVI-175")
    evo1 = make_card("PAF-008")   # Charmeleon - Stage 1
    evo2 = make_card("SVI-086")   # Gardevoir ex - Stage 2
    basic = make_card("PAF-007")  # Charmander - Basic (not a candidate)
    state = make_state(PlayerZones(hand=[jacq], left=[evo1, evo2, basic]))

    actions = jacq.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseSupporterAction)

    prompts = drive_choices(
        jacq.reduce_action(actions[0], state),
        [lambda _info: [evo1, evo2]],
    )

    assert prompts[0]["prompt"].source is jacq
    assert set(prompts[0]["prompt"].candidates) == {evo1, evo2}
    assert evo1 in state.player1.hand
    assert evo2 in state.player1.hand
    assert basic not in state.player1.hand
    assert jacq in state.player1.discard
    assert state.player1.supporterPlayedTurn is True


def test_jacq_unavailable_when_supporter_already_played():
    jacq = make_card("SVI-175")
    state = make_state(PlayerZones(hand=[jacq], left=[make_card("PAF-008")]))
    state.player1.supporterPlayedTurn = True

    assert jacq.get_actions(state) == []
