from __future__ import annotations

from ptcg import PokemonTCG


def _setup_signature(env: PokemonTCG) -> tuple:
    _obs, _reward, done, info = env.reset()
    assert done is False

    # Both players choose their opening Active Pokemon through the public API.
    for _ in range(2):
        action = info["raw_available_actions"][0]
        _obs, _reward, done, info = env.step(action)

    state = env.gamestate
    return (
        tuple(card.id for card in state.player1.hand),
        tuple(card.id for card in state.player1.prize),
        tuple(card.id for card in state.player2.hand),
        tuple(card.id for card in state.player2.prize),
        state.turn,
    )


def test_same_seed_reproduces_setup_without_calling_set_seed():
    first = _setup_signature(PokemonTCG(seed=42, record_game=False))
    second = _setup_signature(PokemonTCG(seed=42, record_game=False))

    assert first == second


def test_environment_randomness_is_isolated_when_games_are_interleaved():
    expected = _setup_signature(PokemonTCG(seed=42, record_game=False))

    env = PokemonTCG(seed=42, record_game=False)
    _obs, _reward, _done, info = env.reset()

    # Another environment must not advance this environment's random stream.
    other = PokemonTCG(seed=999, record_game=False)
    _setup_signature(other)

    for _ in range(2):
        _obs, _reward, _done, info = env.step(info["raw_available_actions"][0])

    state = env.gamestate
    actual = (
        tuple(card.id for card in state.player1.hand),
        tuple(card.id for card in state.player1.prize),
        tuple(card.id for card in state.player2.hand),
        tuple(card.id for card in state.player2.prize),
        state.turn,
    )
    assert actual == expected
