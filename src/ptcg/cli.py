"""Command-line entry point for simulations and interactive matches."""

from __future__ import annotations

import argparse
import random
import sys
from collections.abc import Sequence

from ptcg.core.action import Action
from ptcg.core.envs import PokemonTCG


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ptcg",
        description="Run a Pokemon TCG engine simulation.",
        epilog="For an interactive match, run: ptcg play --help",
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


def build_play_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ptcg play",
        description="Play an interactive Pokemon TCG match against a built-in policy.",
    )
    parser.add_argument("--deck", help="Deck name or path for the human player.")
    parser.add_argument("--opponent-deck", help="Deck name or path for the opponent.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed. Defaults to 0.")
    parser.add_argument(
        "--max-steps",
        type=_positive_int,
        default=1000,
        help="Maximum number of engine actions. Defaults to 1000.",
    )
    parser.add_argument(
        "--opponent-policy",
        choices=("first", "random"),
        default="random",
        help="Opponent action policy. Defaults to random.",
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
    return parser


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def select_action(actions: Sequence[Action], policy: str, rng: random.Random) -> Action:
    if policy == "random":
        return rng.choice(actions)
    return actions[0]


def describe_action(action: Action) -> str:
    try:
        return action.to_nl()
    except Exception:  # noqa: BLE001 - action renderers are third-party card code
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


def run_play(args: argparse.Namespace) -> int:
    from ptcg.console import PlayConfig, RichTerminal, run_interactive

    config = PlayConfig(
        deck=args.deck,
        opponent_deck=args.opponent_deck,
        opponent_policy=args.opponent_policy,
        seed=args.seed,
        max_steps=args.max_steps,
        record=args.record,
        verbose=args.verbose,
    )
    result = run_interactive(config, RichTerminal())
    return result.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv) if argv is not None else sys.argv[1:]
    if arguments and arguments[0] == "play":
        return run_play(build_play_parser().parse_args(arguments[1:]))

    parser = build_parser()
    args = parser.parse_args(arguments)
    return run(args)
