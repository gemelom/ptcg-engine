import pytest

from ptcg.core.action import PutStadiumAction
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("BRS-137")
@pytest.mark.card_coverage(
    "BRS-137",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_collapsed_stadium_discards_extra_benched_pokemon_for_both_players():
    collapsed_stadium = make_card("BRS-137")
    player_bench = [make_card("PAF-007") for _ in range(5)]
    opponent_bench = [make_card("PAF-027") for _ in range(5)]
    state = make_state(
        PlayerZones(hand=[collapsed_stadium], bench=player_bench),
        PlayerZones(bench=opponent_bench),
    )

    actions = collapsed_stadium.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], PutStadiumAction)

    prompts = drive_choices(
        collapsed_stadium.reduce_action(actions[0], state),
        [
            lambda _info: [player_bench[0]],
            lambda _info: [opponent_bench[0]],
        ],
    )

    assert prompts[0]["prompt"].source is collapsed_stadium
    assert prompts[1]["prompt"].source is collapsed_stadium
    assert state.stadium == [collapsed_stadium]
    assert collapsed_stadium not in state.player1.hand
    assert state.player1.benchSize == 4
    assert state.player2.benchSize == 4
    assert len(state.player1.bench) == 4
    assert len(state.player2.bench) == 4
    assert player_bench[0] not in state.player1.bench
    assert opponent_bench[0] not in state.player2.bench
    assert [card.name for card in state.player1.discard] == ["Charmander"]
    assert [card.name for card in state.player2.discard] == ["Ralts"]


def test_collapsed_stadium_is_unavailable_after_stadium_played_this_turn():
    collapsed_stadium = make_card("BRS-137")
    state = make_state(PlayerZones(hand=[collapsed_stadium]))
    state.player1.stadiumPlayedTurn = True

    assert collapsed_stadium.get_actions(state) == []
