"""Test raw environment functionality."""

from ptcg.core.envs import PokemonTCG


def test_env_reset():
    """Test that environment can be reset."""
    env = PokemonTCG(seed=1)
    obs, reward, done, info = env.reset()

    assert env.gamestate is not None
    assert "raw_available_actions" in info
    assert "turn" in info


def test_env_step():
    """Test that environment can step through a game."""
    env = PokemonTCG(seed=1)
    obs, reward, done, info = env.reset()

    # Run until game ends
    max_steps = 1000
    for _ in range(max_steps):
        if done:
            break
        actions = info["raw_available_actions"]
        if actions:
            action = actions[0]  # Take first available action
            obs, reward, done, info = env.step(action)

    assert done, f"Game should end within {max_steps} steps"
