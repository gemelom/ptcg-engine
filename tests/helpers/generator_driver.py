from __future__ import annotations

import copy
from collections.abc import Callable, Generator, Iterable
from typing import Any

from ptcg.core.action import ChooseCardAction
from ptcg.core.card import Card

ChoiceSelector = Callable[[dict], Iterable[Card]]


def drive_choices(generator: Generator, selectors: list[ChoiceSelector]) -> list[dict[str, Any]]:
    """Run a reducer generator and answer each card-choice prompt.

    Each selector receives the yielded info dict and returns the cards to choose.
    The helper sends the matching ChooseCardAction from raw_available_actions back
    into the reducer, which keeps tests aligned with normal engine validation.
    """

    yielded_infos: list[dict[str, Any]] = []

    try:
        _obs, _reward, _done, info = next(generator)
        yielded_infos.append(_snapshot_info(info))
        for selector in selectors:
            chosen = list(selector(info))
            action = _find_matching_choice(info["raw_available_actions"], chosen)
            _obs, _reward, _done, info = generator.send(action)
            yielded_infos.append(_snapshot_info(info))
        raise AssertionError("Generator yielded more prompts than selectors supplied")
    except StopIteration:
        return yielded_infos


def _snapshot_info(info: dict[str, Any]) -> dict[str, Any]:
    snapshot = dict(info)
    prompt = snapshot.get("prompt")
    if prompt is not None:
        prompt = copy.copy(prompt)
        prompt.candidates = list(prompt.candidates)
        snapshot["prompt"] = prompt
    return snapshot


def _find_matching_choice(actions: list[ChooseCardAction], chosen: list[Card]) -> ChooseCardAction:
    for action in actions:
        if action.chosen == chosen:
            return action
    available = [[card.name for card in action.chosen] for action in actions]
    wanted = [card.name for card in chosen]
    raise AssertionError(f"No ChooseCardAction for {wanted}; available choices: {available}")
