import pytest
from unittest.mock import patch

from ptcg.core.action import UseItemAction
from ptcg.core.enums import Coin
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SIT-153")
@pytest.mark.card_coverage(
    "SIT-153",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_capturing_aroma_heads_searches_evolution_pokemon():
    card = make_card("SIT-153")
    evolution = make_card("PAF-008")   # Charmeleon - Stage 1
    basic = make_card("PAF-007")       # Charmander - Basic
    state = make_state(PlayerZones(hand=[card], left=[evolution, basic]))

    actions = card.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    with patch("ptcg.utils.utils.random.randint", return_value=0):  # HEAD
        prompts = drive_choices(
            card.reduce_action(actions[0], state),
            [lambda _info: [evolution]],
        )

    assert prompts[0]["prompt"].source is card
    assert prompts[0]["prompt"].candidates == [evolution]
    assert evolution in state.player1.hand
    assert card in state.player1.discard


def test_capturing_aroma_tails_searches_basic_pokemon():
    card = make_card("SIT-153")
    evolution = make_card("PAF-008")   # Charmeleon - Stage 1
    basic = make_card("PAF-007")       # Charmander - Basic
    state = make_state(PlayerZones(hand=[card], left=[evolution, basic]))

    with patch("ptcg.utils.utils.random.randint", return_value=1):  # TAIL
        prompts = drive_choices(
            card.reduce_action(card.get_actions(state)[0], state),
            [lambda _info: [basic]],
        )

    assert prompts[0]["prompt"].candidates == [basic]
    assert basic in state.player1.hand
    assert card in state.player1.discard


def test_capturing_aroma_unavailable_when_not_in_hand():
    card = make_card("SIT-153")
    state = make_state(PlayerZones(discard=[card]))

    assert card.get_actions(state) == []
