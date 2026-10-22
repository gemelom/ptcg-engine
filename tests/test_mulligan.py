"""Setup-stage mulligan compensation (official optional bonus draw).

Official rule (2026 Pokémon TCG Rulebook, Advanced Rules "Full details of taking
a mulligan"): when a player has no Basic Pokémon in their opening hand they
reveal it, shuffle it back, and redraw until they have a Basic. For each extra
mulligan their opponent *may* draw one extra card. That draw happens after the
opponent has finished setting up and before the first turn, and the opponent
chooses how many (0..N) to take.

These tests script the shuffle order instead of relying on lucky seeds, so the
mulligan count of each seat is exact and the tests stay fast and deterministic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ptcg import PokemonTCG
from ptcg.core.action import MulliganDrawAction, PassTurn
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, PlayerId, Stage
from ptcg.core.exceptions import InvalidActionError
from ptcg.core.player import Player
from ptcg.utils.load_deck import load_deck

BASIC_CARD = "1 Charmander PAF 7"
ENERGY_CARD = "59 Basic {R} Energy SVE 2"


# --------------------------------------------------------------------- helpers


def _is_basic(card) -> bool:
    return isinstance(card, PokemonCard) and card.stage == Stage.BASIC


class _ScriptedShuffleRng:
    """Deterministic RNG: each shuffle puts Basics first or last by script.

    ``plan[i]`` is True when call *i* should put Basic Pokémon on top (a valid
    opening hand) and False when it should bury them (one mulligan). The coin
    flip is fixed by ``coin`` (0 = heads).
    """

    def __init__(self, plan: list[bool], coin: int = 0) -> None:
        self.plan = list(plan)
        self.calls = 0
        self.coin = coin

    def shuffle(self, cards) -> None:
        basics_first = self.plan[self.calls] if self.calls < len(self.plan) else True
        self.calls += 1
        basics = [card for card in cards if _is_basic(card)]
        others = [card for card in cards if not _is_basic(card)]
        cards[:] = basics + others if basics_first else others + basics

    def randint(self, low: int, high: int) -> int:
        return self.coin if (low, high) == (0, 1) else low

    def choice(self, sequence):
        return sequence[0]


def _deck_file(tmp_path: Path) -> str:
    path = tmp_path / "one_basic.txt"
    path.write_text(f"{BASIC_CARD}\n{ENERGY_CARD}\n", encoding="utf-8")
    return str(path)


def _make_env(tmp_path: Path, plan: list[bool], *, coin: int = 0, seed: int = 0):
    deck_path = _deck_file(tmp_path)
    env = PokemonTCG(seed=seed, deck1=deck_path, deck2=deck_path, record_game=False)
    env.rng = _ScriptedShuffleRng(plan, coin=coin)
    return env


def _drive_setup(env, draws: str | dict[int, int] = "decline"):
    """Play through Active selection and mulligan compensation.

    ``draws`` is "decline", "all", or a mapping of prompt index to card count.
    Returns the offered prompt lists, the actor per prompt, the observation
    viewer per prompt, and the first-turn result.
    """
    result = env.reset()
    prompts: list[list[MulliganDrawAction]] = []
    actors: list[PlayerId] = []
    viewers: list[str] = []
    while True:
        raw = result[3]["raw_available_actions"]
        if hasattr(raw, "action_for_candidate_indices"):
            result = env.step(raw.action_for_candidate_indices([0]))
            continue
        if raw and isinstance(raw[0], MulliganDrawAction):
            offered = list(raw)
            prompts.append(offered)
            actors.append(env.gamestate.turn)
            viewers.append(result[0]["viewer"])
            if draws == "all":
                count = offered[-1].count
            elif draws == "decline":
                count = 0
            else:
                count = draws.get(len(prompts) - 1, 0)
            chosen = next(action for action in offered if action.count == count)
            result = env.step(chosen)
            continue
        return prompts, actors, viewers, result


def _state_signature(env) -> str:
    state = env.gamestate
    payload = {
        "p1_hand": [card.id for card in state.player1.hand],
        "p2_hand": [card.id for card in state.player2.hand],
        "p1_left": [card.id for card in state.player1.left],
        "p2_left": [card.id for card in state.player2.left],
        "p1_prize": [card.id for card in state.player1.prize],
        "p2_prize": [card.id for card in state.player2.prize],
        "turn": state.turn.value if state.turn else None,
        "first_player": (
            state.first_player_id.value if state.first_player_id else None
        ),
        "timestep": state.timestep,
    }
    return json.dumps(payload, sort_keys=True)


# ------------------------------------------------------------ shuffle counting


@pytest.mark.parametrize("mulligans", [0, 1, 2])
def test_player_shuffle_counts_mulligans_and_deals_correct_zones(
    tmp_path: Path, mulligans: int
) -> None:
    deck = load_deck(_deck_file(tmp_path))
    player = Player(deck)
    player.id = PlayerId.PLAYER1
    rng = _ScriptedShuffleRng([False] * mulligans + [True])

    player.shuffle(rng)

    assert player.mulligan_count == mulligans
    assert rng.calls == mulligans + 1
    assert (len(player.hand), len(player.prize), len(player.left)) == (7, 6, 47)
    assert len(player.deck) == 60
    assert any(_is_basic(card) for card in player.hand)


@pytest.mark.parametrize("mulligans", [0, 1, 2, 5])
def test_shuffle_consumes_exactly_one_rng_call_per_deal(
    tmp_path: Path, mulligans: int
) -> None:
    deck = load_deck(_deck_file(tmp_path))
    player = Player(deck)
    player.id = PlayerId.PLAYER1
    rng = _ScriptedShuffleRng([False] * mulligans + [True])

    player.shuffle(rng)

    assert player.mulligan_count == mulligans
    assert rng.calls == mulligans + 1, "one shuffle per deal, no extra RNG calls"


# ------------------------------------------------------------------- env tests


def test_zero_mulligans_offers_no_prompt(tmp_path: Path) -> None:
    env = _make_env(tmp_path, plan=[True, True])

    prompts, actors, viewers, result = _drive_setup(env)

    assert prompts == []
    assert actors == []
    assert viewers == []
    state = env.gamestate
    assert state.player1.mulligan_count == 0
    assert state.player2.mulligan_count == 0
    assert state.timestep == 0
    assert state.first_player_id is not None
    assert state.turn == state.first_player_id
    for player in (state.player1, state.player2):
        assert len(player.hand) == 6  # seven dealt, one placed as Active
        assert len(player.prize) == 6
        assert len(player.left) == 47
    assert not any(
        isinstance(action, MulliganDrawAction)
        for action in result[3]["raw_available_actions"]
    )


def test_single_mulligan_offers_decline_and_draw(tmp_path: Path) -> None:
    # Player 1 mulligans once; player 2's opening hand is valid.
    env = _make_env(tmp_path, plan=[False, True, True])

    prompts, actors, viewers, result = _drive_setup(env, draws={0: 1})

    state = env.gamestate
    assert state.player1.mulligan_count == 1
    assert state.player2.mulligan_count == 0
    assert actors == [PlayerId.PLAYER2], "only the opponent of the mulligan is asked"
    assert viewers == ["player2"], "the prompt is shown from the chooser's view"
    offered = prompts[0]
    assert [action.count for action in offered] == [0, 1]
    assert all(action.playerId == PlayerId.PLAYER2 for action in offered)
    assert all(action.max_count == 1 for action in offered)
    assert offered[0].to_nl() == "Player2 declined the bonus draw for 1 extra mulligan"
    assert offered[1].to_nl() == "Player2 drew 1 bonus card for 1 extra mulligan"
    assert offered[1].to_dict()["count"] == 1
    assert offered[1].to_dict()["max_count"] == 1
    assert offered[1].to_dict()["actionType"] == "MulliganDrawAction"

    # The chooser accepted exactly one card.
    assert len(state.player2.hand) == 7
    assert len(state.player2.left) == 46
    assert len(state.player1.hand) == 6
    assert len(state.player1.left) == 47
    assert any(
        "PLAYER2 drew 1 bonus card for 1 extra mulligan." in event
        for event in result[3].get("auto_executed", [])
    )
    assert result[3]["is_choosing_card"] is False
    assert "prompt" not in result[3]
    assert state.turn == state.first_player_id


def test_two_mulligans_accept_all_draws_two(tmp_path: Path) -> None:
    env = _make_env(tmp_path, plan=[False, False, True, True])

    prompts, actors, _viewers, result = _drive_setup(env, draws="all")

    state = env.gamestate
    assert state.player1.mulligan_count == 2
    assert actors == [PlayerId.PLAYER2]
    assert [action.count for action in prompts[0]] == [0, 1, 2]
    assert [action.max_count for action in prompts[0]] == [2, 2, 2]
    assert prompts[0][2].to_nl() == "Player2 drew 2 bonus cards for 2 extra mulligans"
    assert len(state.player2.hand) == 8
    assert len(state.player2.left) == 45
    assert any(
        "PLAYER2 drew 2 bonus cards for 2 extra mulligans." in event
        for event in result[3].get("auto_executed", [])
    )


def test_declining_is_legal_and_changes_nothing(tmp_path: Path) -> None:
    env = _make_env(tmp_path, plan=[False, False, True, True])

    prompts, _actors, _viewers, result = _drive_setup(env, draws="decline")

    state = env.gamestate
    assert prompts[0][0].count == 0
    assert len(state.player2.hand) == 6
    assert len(state.player2.left) == 47
    assert len(state.player1.hand) == 6
    assert result[3]["turn"] == state.first_player_id


def test_equal_mulligans_cancel_the_bonus_draw(tmp_path: Path) -> None:
    # Both seats mulligan twice: the simultaneous restarts do not compensate.
    env = _make_env(tmp_path, plan=[False, False, True, False, False, True])

    prompts, actors, viewers, result = _drive_setup(env, draws="all")

    state = env.gamestate
    assert (state.player1.mulligan_count, state.player2.mulligan_count) == (2, 2)
    assert prompts == [], "equal mulligan counts must not produce a bonus draw"
    assert actors == [] and viewers == []
    for player in (state.player1, state.player2):
        assert len(player.hand) == 6
        assert len(player.left) == 47
    assert result[3]["turn"] == state.first_player_id


def test_both_players_mulligan_pay_only_the_difference(tmp_path: Path) -> None:
    # Rulebook example: both take 2 mulligans, then player 2 takes 3 more, so
    # the counts are 2 vs 5 and only player 1 may draw up to 3 cards.
    env = _make_env(tmp_path, plan=[False, False, True, False, False, False, False, False, True])

    prompts, actors, viewers, result = _drive_setup(env, draws="all")

    state = env.gamestate
    assert (state.player1.mulligan_count, state.player2.mulligan_count) == (2, 5)
    assert actors == [PlayerId.PLAYER1], "only the seat with fewer mulligans draws"
    assert viewers == ["player1"]
    offered = prompts[0]
    assert [action.count for action in offered] == [0, 1, 2, 3]
    assert all(action.max_count == 3 for action in offered)
    assert offered[0].to_nl() == "Player1 declined the bonus draw for 3 extra mulligans"
    assert offered[3].to_nl() == "Player1 drew 3 bonus cards for 3 extra mulligans"
    assert len(state.player1.hand) == 9  # six after Active + 3 bonus
    assert len(state.player1.left) == 44
    assert len(state.player2.hand) == 6
    assert len(state.player2.left) == 47
    assert any(
        "PLAYER1 drew 3 bonus cards for 3 extra mulligans." in event
        for event in result[3].get("auto_executed", [])
    )


def test_bonus_draw_does_not_leak_card_identity_to_opponent(tmp_path: Path) -> None:
    env = _make_env(tmp_path, plan=[False, True, True])
    env.reset()
    # Walk to the mulligan prompt so the deck top is about to be drawn.
    result = env.step(env.cur_available_actions.action_for_candidate_indices([0]))
    result = env.step(result[3]["raw_available_actions"].action_for_candidate_indices([0]))
    assert isinstance(result[3]["raw_available_actions"][0], MulliganDrawAction)

    canary = "CANARY-MULLIGAN-7f3a"
    state = env.gamestate
    drawn = state.player2.left[0]
    drawn.name = canary

    choice = next(a for a in result[3]["raw_available_actions"] if a.count == 1)
    _obs, _reward, _done, info = env.step(choice)

    assert any(card.name == canary for card in state.player2.hand)
    own_view = json.dumps(state.get_obs(state.player2.id))
    opponent_view = json.dumps(state.get_obs(state.player1.id))
    assert canary in own_view, "the chooser may see their own drawn card"
    assert canary not in opponent_view, "the bonus draw leaked to the other seat"
    assert canary not in json.dumps(info.get("auto_executed", []))


def test_deck_out_edge_caps_offered_draws_at_remaining_deck(tmp_path: Path) -> None:
    # 54 mulligans: the opponent's official maximum exceeds the 47 cards left.
    env = _make_env(tmp_path, plan=[False] * 54 + [True, True])

    prompts, actors, _viewers, result = _drive_setup(env, draws="all")

    state = env.gamestate
    assert state.player1.mulligan_count == 54
    assert actors == [PlayerId.PLAYER2]
    offered = prompts[0]
    assert offered[-1].max_count == 54
    assert [action.count for action in offered] == list(range(48))
    assert offered[-1].count == 47
    assert len(state.player2.hand) == 53  # six kept after the Active + 47 bonus
    assert len(state.player2.left) == 0

    # The emptied deck loses only when its owner must draw at the start of a turn.
    pass_turn = next(
        action
        for action in result[3]["raw_available_actions"]
        if isinstance(action, PassTurn)
    )
    _obs, _reward, done, final_info = env.step(pass_turn)

    assert done is True
    assert final_info["winner"] == PlayerId.PLAYER1
    assert final_info["termination_reason"] == "deck_out"


def test_mulligan_choice_is_offered_through_env_validation(tmp_path: Path) -> None:
    env = _make_env(tmp_path, plan=[False, True, True])
    env.reset()
    result = env.step(env.cur_available_actions.action_for_candidate_indices([0]))
    result = env.step(result[3]["raw_available_actions"].action_for_candidate_indices([0]))
    offered = list(result[3]["raw_available_actions"])
    assert env.cur_available_actions is result[3]["raw_available_actions"]
    assert all(action in env.cur_available_actions for action in offered)

    stale = MulliganDrawAction(PlayerId.PLAYER2, env.gamestate.player2, count=1, max_count=1)
    with pytest.raises(InvalidActionError, match="not available"):
        env.step(stale)

    # The rejected action did not advance the game; the offered action still works.
    _obs, _reward, _done, info = env.step(offered[1])
    assert info["turn"] is not None


def test_mulligan_action_rejects_impossible_counts(tmp_path: Path) -> None:
    deck = load_deck(_deck_file(tmp_path))
    player = Player(deck)
    player.id = PlayerId.PLAYER1

    with pytest.raises(ValueError, match="count"):
        MulliganDrawAction(PlayerId.PLAYER1, player, count=2, max_count=1)
    with pytest.raises(ValueError, match="max_count"):
        MulliganDrawAction(PlayerId.PLAYER1, player, count=0, max_count=-1)


def _real_seed_with_bonus(deck_path: str, limit: int = 60) -> int:
    """Find a real-RNG seed where the two seats mulliganed a different number of times."""
    for seed in range(limit):
        env = PokemonTCG(seed=seed, deck1=deck_path, deck2=deck_path, record_game=False)
        prompts, _actors, _viewers, _result = _drive_setup(env, draws="decline")
        if prompts:
            return seed
    raise AssertionError("no seed produced an uneven mulligan count")


def test_same_seed_reproduces_mulligans_and_bonus_draws(tmp_path: Path) -> None:
    deck_path = _deck_file(tmp_path)
    seed = _real_seed_with_bonus(deck_path)

    def run(draws: str) -> tuple[list[list[tuple[int, int]]], str, int]:
        env = PokemonTCG(seed=seed, deck1=deck_path, deck2=deck_path, record_game=False)
        prompts, _actors, _viewers, _result = _drive_setup(env, draws=draws)
        shape = [
            [(action.count, action.max_count) for action in offered] for offered in prompts
        ]
        hands = len(env.gamestate.player1.hand) + len(env.gamestate.player2.hand)
        return shape, _state_signature(env), hands

    first_shape, first_state, all_hands = run("all")
    second_shape, second_state, second_all_hands = run("all")

    assert first_shape, f"seed {seed} must exercise a mulligan bonus draw"
    assert first_shape == second_shape
    assert first_state == second_state
    assert all_hands == second_all_hands

    decline_shape, _decline_state, decline_hands = run("decline")
    assert decline_shape == first_shape, "the offered options must not depend on the choice"
    assert all_hands - decline_hands == sum(offered[-1][1] for offered in first_shape)


def test_prompt_keeps_zone_positions_and_choice_flag(tmp_path: Path) -> None:
    """The setup prompt must not mark a card-selection state or reorder zones."""
    env = _make_env(tmp_path, plan=[False, True, True])
    env.reset()
    first = env.step(env.cur_available_actions.action_for_candidate_indices([0]))
    first_info = first[3]
    assert first_info["is_choosing_card"] is True  # still the Active prompt

    second = env.step(first_info["raw_available_actions"].action_for_candidate_indices([0]))
    prompt_info = second[3]
    assert prompt_info["is_choosing_card"] is False
    assert "prompt" not in prompt_info
    state = env.gamestate
    for player in (state.player1, state.player2):
        for zone, position in (
            (player.hand, CardPosition.HAND),
            (player.prize, CardPosition.PRIZE),
            (player.left, CardPosition.LEFT),
        ):
            for index, card in enumerate(zone, start=1):
                assert card.cardPosition == position
                assert card.index == index
