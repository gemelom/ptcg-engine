# Contributing and Maintenance

`ptcg-engine` is an alpha simulation engine. Prefer small, rule-focused changes that
preserve deterministic runs and make failures easy to diagnose.

## Quality Gate

Install the exact locked environment and run the same checks as CI:

```bash
uv sync --frozen --all-groups
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov=ptcg --cov-report=term-missing --cov-fail-under=90
uv run python scripts/card_test_coverage.py --fail-on-unknown
uv run pip-audit
uv build
```

Keep a behavior fix or optimization and its tests in one commit. Do not combine
unrelated cleanup with a rules change; isolated commits make regressions and rule
disagreements practical to bisect or revert.

## Engine Invariants

- Each `PokemonTCG` environment owns its random-number generator. Route randomness
  through `state.rng` or an existing state-aware helper; do not use process-global
  seeding.
- `get_actions()` exposes only actions that are legal in the current state.
  Reducers reject unavailable or malformed actions instead of silently substituting one.
- Attack definitions on cards are templates. Modify the action-local `AttackAction.attack`
  copy for variable damage or temporary modifiers.
- Multi-step player input uses `choose_card_actions()` and
  `reduce_choose_card_actions()`. Mark choices from private zones as `hidden=True` and
  set `source=` so callers can identify the effect that opened the prompt.
- Public observations are detached and player-relative. Never expose mutable `State`,
  deck identities, Prize identities, or the opponent's hand unless the caller explicitly
  enables the debugging-only `expose_full_state` option.
- Use the shared reducers for attacks, knockouts, prizes, retreat, evolution, and zone
  moves. This keeps passive abilities, automatic events, termination, and turn changes
  on one lifecycle path.

## Adding or Changing a Card

1. Confirm the exact printing and wording in the official
   [Pokémon TCG Card Database](https://www.pokemon.com/uk/pokemon-tcg/pokemon-cards)
   and consult the official
   [Pokémon TCG rulebook](https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/par_rulebook_en.pdf)
   for shared rules. Record a source URL in a comment when an implementation depends on
   a non-obvious ruling.
2. Add a failing direct test first. Mark one rule-focused test with
   `@pytest.mark.card("SET-NNN")` and list the exercised behaviors with
   `@pytest.mark.card_coverage(...)`.
3. Cover the successful effect, action availability, at least one negative case, and
   relevant edge cases such as an undersized deck, a full Bench, knockout, or a choice
   with duplicate card names.
4. Implement the smallest reducer change that satisfies the card text. Reuse existing
   action and reducer interfaces before adding a card-specific state path.
5. Run the card's test module, then the complete quality gate above. The card coverage
   report must not contain unknown IDs, and every implemented card should retain a direct
   test.

## Scope and Known Limits

- The supported rule surface is the implemented card pool under `src/ptcg/cards`, not
  every card or interaction in the official game.
- Card coverage markers prove that named behavior has a direct test; they are not a
  claim of exhaustive rules conformance.
- Static typing currently gates `src/ptcg/core`. Extend it into cards and utilities in
  small batches while keeping the gate green.
- The `0.x` API may change as rule coverage grows. Treat observations and action classes
  as evolving interfaces until a stable compatibility policy is published.
