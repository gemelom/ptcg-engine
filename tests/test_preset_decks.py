import pytest

from ptcg.core.action import PassTurn
from ptcg.core.envs import PokemonTCG


def _run_smoke(deck_name: str, steps: int = 30) -> None:
    """Load a preset deck vs itself, run up to `steps` steps without error."""
    env = PokemonTCG(seed=42, deck1=deck_name, deck2=deck_name)
    _obs, _reward, done, info = env.reset()

    for _ in range(steps):
        if done:
            break
        actions = info.get("raw_available_actions", [])
        if not actions:
            break
        action = next((a for a in actions if isinstance(a, PassTurn)), actions[0])
        _obs, _reward, done, info = env.step(action)


@pytest.mark.parametrize(
    "deck_name",
    ["charizard_ex", "gardevori_ex", "gholdengo_ex", "lugia_archeops", "miraidon_ex"],
)
def test_preset_deck_loads_and_runs(deck_name: str) -> None:
    _run_smoke(deck_name)
