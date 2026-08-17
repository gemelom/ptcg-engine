from __future__ import annotations

import itertools

from ptcg import PokemonTCG
from ptcg.core.action import (
    ChooseCardAction,
    ChooseCardActionSpace,
    choose_card_actions,
)
from ptcg.core.enums import PlayerId
from tests.helpers.cards import make_card


def test_choice_action_space_is_lazy_for_exponential_combinations():
    candidates = [make_card("SVE-002") for _ in range(30)]

    actions, _prompt = choose_card_actions(
        PlayerId.PLAYER1,
        PlayerId.PLAYER1,
        0,
        len(candidates),
        candidates,
    )

    assert isinstance(actions, ChooseCardActionSpace)
    assert len(actions) == 2**30
    assert actions[0].chosen == []
    assert actions[-1].chosen == candidates


def test_choice_action_space_preserves_combination_order_and_validation():
    candidates = [make_card("SVE-002") for _ in range(4)]
    actions, _prompt = choose_card_actions(
        PlayerId.PLAYER1,
        PlayerId.PLAYER2,
        1,
        2,
        candidates,
    )
    expected = [
        list(combo) for count in (1, 2) for combo in itertools.combinations(candidates, count)
    ]

    assert [action.chosen for action in actions] == expected
    assert actions[5].chosen == expected[5]
    assert actions[-1].chosen == expected[-1]
    assert actions[2:5][0].chosen == expected[2]

    valid_reconstruction = ChooseCardAction(
        PlayerId.PLAYER1,
        PlayerId.PLAYER2,
        [candidates[0], candidates[2]],
        candidates,
    )
    reversed_choice = ChooseCardAction(
        PlayerId.PLAYER1,
        PlayerId.PLAYER2,
        [candidates[2], candidates[0]],
        candidates,
    )
    duplicate_choice = ChooseCardAction(
        PlayerId.PLAYER1,
        PlayerId.PLAYER2,
        [candidates[0], candidates[0]],
        candidates,
    )

    assert valid_reconstruction in actions
    assert reversed_choice not in actions
    assert duplicate_choice not in actions


def test_environment_keeps_choice_action_space_lazy():
    env = PokemonTCG(seed=42, record_game=False)

    _obs, _reward, _done, info = env.reset()

    assert isinstance(info["raw_available_actions"], ChooseCardActionSpace)
    assert env.cur_available_actions is info["raw_available_actions"]
