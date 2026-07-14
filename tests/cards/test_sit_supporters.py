import pytest

from ptcg.core.action import UseSupporterAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SIT-164")
@pytest.mark.card_coverage(
    "SIT-164",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_serena_effect1_discards_cards_and_draws_to_five():
    serena = make_card("SIT-164")
    hand_cards = [make_card("SVE-002"), make_card("SVE-004"), make_card("SVE-005")]
    deck_cards = [make_card("PAF-007"), make_card("PAF-008"), make_card("PAF-084")]
    state = make_state(PlayerZones(hand=[serena] + hand_cards, left=deck_cards))

    actions = serena.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseSupporterAction)

    to_discard = [hand_cards[0], hand_cards[1]]
    prompts = drive_choices(
        serena.reduce_action(actions[0], state),
        [
            lambda info: [c for c in info["prompt"].candidates if c.name == "Effect 1: Discard & Draw"],
            lambda _info: to_discard,
        ],
    )

    assert all(c in state.player1.discard for c in to_discard)
    assert len(state.player1.hand) == 4  # 1 remaining + 3 drawn (deck had 3)
    assert state.player1.supporterPlayedTurn is True


def test_serena_effect2_switches_opponent_benched_v_with_active():
    serena = make_card("SIT-164")
    opponent_active = make_card("PAF-007")   # non-V active
    benched_v = make_card("SIT-138")         # Lugia V - Pokemon V
    state = make_state(
        PlayerZones(hand=[serena]),
        PlayerZones(active=[opponent_active], bench=[benched_v]),
    )

    prompts = drive_choices(
        serena.reduce_action(serena.get_actions(state)[0], state),
        [
            lambda info: [c for c in info["prompt"].candidates if c.name == "Effect 2: Switch Pokemon V"],
            lambda _info: [benched_v],
        ],
    )

    assert state.player2.active[0] is benched_v
    assert opponent_active in state.player2.bench
    assert state.player1.supporterPlayedTurn is True


def test_serena_unavailable_when_supporter_already_played():
    serena = make_card("SIT-164")
    state = make_state(PlayerZones(hand=[serena, make_card("SVE-002")]))
    state.player1.supporterPlayedTurn = True

    assert serena.get_actions(state) == []


def test_serena_unavailable_with_empty_hand_and_no_opponent_bench():
    serena = make_card("SIT-164")
    state = make_state(PlayerZones(discard=[serena]))  # hand is empty, no opponent bench

    assert serena.get_actions(state) == []
