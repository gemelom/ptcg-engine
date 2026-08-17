from __future__ import annotations

import pytest

from ptcg import PokemonTCG
from ptcg.core.action import PassTurn
from ptcg.core.exceptions import InvalidActionError


def _complete_setup(env: PokemonTCG):
    _obs, _reward, _done, info = env.reset()
    for _ in range(2):
        _obs, _reward, _done, info = env.step(info["raw_available_actions"][0])
    return info


def test_invalid_regular_action_raises_without_mutating_state():
    env = PokemonTCG(seed=42, record_game=False)
    info = _complete_setup(env)
    state = info["full_state"]
    timestep = state.timestep
    recorded_actions = list(state.actions_buffer)
    invalid_action = PassTurn(state.turn, state.player1)

    with pytest.raises(InvalidActionError, match="not available"):
        env.step(invalid_action)

    assert state.timestep == timestep
    assert state.actions_buffer == recorded_actions


def test_invalid_card_choice_raises_before_closing_game_generator():
    env = PokemonTCG(seed=42, record_game=False)
    _obs, _reward, _done, info = env.reset()
    invalid_action = PassTurn(info["turn"], env.gamestate.player1)

    with pytest.raises(InvalidActionError, match="not available"):
        env.step(invalid_action)

    valid_action = info["raw_available_actions"][0]
    _obs, _reward, done, next_info = env.step(valid_action)

    assert done is False
    assert next_info["is_choosing_card"] is True


def test_random_policy_explicitly_replaces_invalid_action():
    env = PokemonTCG(seed=42, record_game=False, invalid_action_policy="random")
    _obs, _reward, _done, info = env.reset()
    invalid_action = PassTurn(info["turn"], env.gamestate.player1)

    _obs, _reward, done, next_info = env.step(invalid_action)

    assert done is False
    assert env.gamestate.player1.active
    assert next_info["is_choosing_card"] is True


def test_invalid_action_policy_is_validated():
    with pytest.raises(ValueError, match="invalid_action_policy"):
        PokemonTCG(invalid_action_policy="ignore")
