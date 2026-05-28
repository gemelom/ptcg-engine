"""Command-line entry point for running Pokemon TCG simulations."""

from __future__ import annotations

import argparse
import random
from collections.abc import Sequence
from typing import Optional

from ptcg.core.action import Action
from ptcg.core.envs import PokemonTCG


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ptcg",
        description="Run a Pokemon TCG engine simulation.",
    )
    parser.add_argument("--deck1", help="Deck name or path for player 1.")
    parser.add_argument("--deck2", help="Deck name or path for player 2.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed. Defaults to 0.")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=1000,
        help="Maximum number of actions to run before stopping. Defaults to 1000.",
    )
    parser.add_argument(
        "--policy",
        choices=("first", "random"),
        default="first",
        help="Action selection policy. Defaults to first.",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record the game with the engine recorder.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose engine logging.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the final result.",
    )
    return parser


def select_action(actions: Sequence[Action], policy: str, rng: random.Random) -> Action:
    if policy == "random":
        return rng.choice(actions)
    return actions[0]


def describe_action(action: Action) -> str:
    try:
        return action.to_nl()
    except Exception:
        return repr(action)


def run(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed)

    env = PokemonTCG(
        seed=args.seed,
        deck1=args.deck1,
        deck2=args.deck2,
        verbose=args.verbose,
        record_game=args.record,
    )
    env.set_seed(args.seed)

    _obs, reward, done, info = env.reset()
    steps = 0

    while not done and steps < args.max_steps:
        actions = info.get("raw_available_actions", [])
        if not actions:
            print(f"No available actions at step {steps}.")
            return 2

        action = select_action(actions, args.policy, rng)
        if not args.quiet:
            turn = info.get("turn")
            print(f"{steps + 1:04d} {turn}: {describe_action(action)}")

        _obs, reward, done, info = env.step(action)
        steps += 1

    winner = info.get("winner") or env.winner
    if done:
        print(f"Game finished in {steps} steps. Winner: {winner}. Reward: {reward}.")
        return 0

    print(f"Stopped after {steps} steps without a winner. Last reward: {reward}.")
    return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)
