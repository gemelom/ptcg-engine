#!/usr/bin/env python3
"""Report card-specific test coverage from pytest markers.

The report is intentionally separate from coverage.py. Line coverage tells us
which code executed; this script tracks whether each implemented card has
explicit rule-focused tests.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TESTS = ROOT / "tests"

FEATURES = (
    "metadata",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ko",
    "ability",
    "deck_smoke",
)


@dataclass
class MarkerHit:
    path: str
    test_name: str
    features: set[str] = field(default_factory=set)


def _ensure_import_path() -> None:
    src = str(SRC)
    if src not in sys.path:
        sys.path.insert(0, src)


def implemented_cards() -> list[str]:
    _ensure_import_path()
    from ptcg.core.card_registry import registry

    return sorted(registry.list_all())


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _literal_string_list(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = []
        for item in node.elts:
            value = _literal_string(item)
            if value is not None:
                values.append(value)
        return values
    value = _literal_string(node)
    return [value] if value is not None else []


def _pytest_mark_name(decorator: ast.AST) -> str | None:
    call = decorator if isinstance(decorator, ast.Call) else None
    target = call.func if call else decorator
    if not isinstance(target, ast.Attribute):
        return None
    if not isinstance(target.value, ast.Attribute):
        return None
    if target.value.attr != "mark":
        return None
    if not isinstance(target.value.value, ast.Name):
        return None
    if target.value.value.id != "pytest":
        return None
    return target.attr


def _marker_args(decorator: ast.AST) -> tuple[list[str], list[str]]:
    if not isinstance(decorator, ast.Call):
        return ([], [])

    cards: list[str] = []
    features: list[str] = []
    if decorator.args:
        cards.extend(_literal_string_list(decorator.args[0]))
        for arg in decorator.args[1:]:
            features.extend(_literal_string_list(arg))

    for keyword in decorator.keywords:
        if keyword.arg in {"card", "cards", "card_id", "card_ids"}:
            cards.extend(_literal_string_list(keyword.value))
        elif keyword.arg in {"feature", "features"}:
            features.extend(_literal_string_list(keyword.value))

    return cards, features


def _iter_test_functions(path: Path) -> Iterable[ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test_"
        ):
            yield node


def collect_marker_hits(tests_dir: Path = TESTS) -> dict[str, list[MarkerHit]]:
    hits: dict[str, list[MarkerHit]] = defaultdict(list)

    for path in sorted(tests_dir.rglob("test_*.py")):
        rel_path = str(path.relative_to(ROOT))
        for test_func in _iter_test_functions(path):
            direct_cards: set[str] = set()
            feature_cards: dict[str, set[str]] = defaultdict(set)

            for decorator in test_func.decorator_list:
                mark_name = _pytest_mark_name(decorator)
                if mark_name not in {"card", "card_coverage"}:
                    continue

                cards, features = _marker_args(decorator)
                if mark_name == "card":
                    direct_cards.update(cards)
                else:
                    if not features:
                        features = ["metadata"]
                    for card in cards:
                        feature_cards[card].update(features)

            all_cards = direct_cards | set(feature_cards)
            for card in sorted(all_cards):
                hits[card].append(
                    MarkerHit(
                        path=rel_path,
                        test_name=test_func.name,
                        features=set(feature_cards.get(card, set())),
                    )
                )

    return dict(hits)


def build_report() -> dict:
    cards = implemented_cards()
    card_set = set(cards)
    hits = collect_marker_hits()

    all_hits = hits.get("ALL", [])
    all_features = set().union(*(hit.features for hit in all_hits)) if all_hits else set()

    per_card = {}
    unknown_cards = sorted(card for card in hits if card != "ALL" and card not in card_set)

    for card in cards:
        card_hits = hits.get(card, [])
        features = set(all_features)
        for hit in card_hits:
            features.update(hit.features)
        per_card[card] = {
            "direct_tests": [
                {"path": hit.path, "test": hit.test_name, "features": sorted(hit.features)}
                for hit in card_hits
            ],
            "features": sorted(features),
        }

    metrics = {
        "implemented_cards": len(cards),
        "cards_with_direct_tests": sum(1 for card in cards if hits.get(card)),
        "cards_with_any_coverage": sum(1 for card in cards if per_card[card]["features"]),
        "unknown_marked_cards": len(unknown_cards),
    }
    for feature in FEATURES:
        metrics[f"cards_with_{feature}"] = sum(
            1 for card in cards if feature in per_card[card]["features"]
        )

    return {
        "metrics": metrics,
        "features": list(FEATURES),
        "unknown_marked_cards": unknown_cards,
        "global_features": sorted(all_features),
        "cards": per_card,
    }


def print_text_report(report: dict) -> None:
    metrics = report["metrics"]
    total = metrics["implemented_cards"]

    print(f"Implemented cards: {total}")
    print(f"Cards with direct tests: {metrics['cards_with_direct_tests']} / {total}")
    print(f"Cards with any marked coverage: {metrics['cards_with_any_coverage']} / {total}")
    print()
    print("Feature coverage:")
    for feature in FEATURES:
        count = metrics[f"cards_with_{feature}"]
        print(f"  {feature}: {count} / {total}")

    if report["global_features"]:
        print()
        print("Global ALL-card features: " + ", ".join(report["global_features"]))

    if report["unknown_marked_cards"]:
        print()
        print("Unknown marked cards:")
        for card in report["unknown_marked_cards"]:
            print(f"  {card}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--fail-on-unknown",
        action="store_true",
        help="exit non-zero if tests mark a card id that is not implemented",
    )
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    if args.fail_on_unknown and report["unknown_marked_cards"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
