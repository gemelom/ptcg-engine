from __future__ import annotations

from ptcg.core.card import Card
from ptcg.core.card_registry import registry


def make_card(card_id: str) -> Card:
    card_class = registry.get(card_id)
    if card_class is None:
        raise AssertionError(f"Unknown card id: {card_id}")
    return card_class()
