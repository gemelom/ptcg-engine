# ptcg-engine

Clean Python game engine for Pokemon TCG simulations.

The distribution package is `ptcg-engine`; the import package is `ptcg`.
This repository intentionally contains only engine code:

- `ptcg.core`
- `ptcg.cards`
- `ptcg.utils`
- bundled deck fixtures in `ptcg.decks`

Agents, benchmarks, backend services, and frontend code live outside this package.

## Status

This project is in alpha. The engine can run deterministic simulations with the bundled
decks, but the supported card pool and rule coverage are still limited to the implemented
cards in `ptcg.cards`.

## Installation

Install from a local checkout:

```bash
uv sync
```

For editable development with standard Python tooling:

```bash
python -m pip install -e .
```

## Quick Start

Run a complete simulated game with the default decks:

```bash
uv run ptcg --quiet
```

The module entry point is also available:

```bash
uv run python -m ptcg --quiet
```

Run with explicit decks and a random action policy:

```bash
uv run ptcg --deck1 charizard_ex --deck2 miraidon_ex --seed 42 --policy random
```

## Python API

```python
from ptcg import PokemonTCG

env = PokemonTCG(seed=42, deck1="charizard_ex", deck2="miraidon_ex")
obs, reward, done, info = env.reset()

while not done:
    actions = info["raw_available_actions"]
    action = actions[0]
    obs, reward, done, info = env.step(action)

print(info["winner"])
```

The environment follows a Gym-like shape:

- `reset()` returns `(obs, reward, done, info)`.
- `step(action)` advances the game and returns `(obs, reward, done, info)`.
- `info["raw_available_actions"]` contains the valid engine action objects.

## Decks

Bundled deck fixtures live in `src/ptcg/decks` and can be referenced by name without
the `.txt` suffix:

- `charizard_ex`
- `gholdengo_ex`
- `miraidon_ex`
- `lugia_archeops`
- `gardevori_ex`

You can also pass a path to a deck text file:

```bash
uv run ptcg --deck1 ./my_deck.txt --deck2 charizard_ex
```

## Development

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

Run lint checks:

```bash
uv run ruff check .
```

Build distributions:

```bash
uv build
```

## Project Boundaries

This package provides a simulation engine and card implementations. It does not include
training agents, benchmark runners, a backend service, or a frontend application.

## Disclaimer

This is an unofficial fan/developer project. It is not affiliated with, endorsed by, or
sponsored by Nintendo, The Pokemon Company, Creatures, or Game Freak. Pokemon and Pokemon
TCG are trademarks of their respective owners.
