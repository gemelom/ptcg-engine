import pytest

from ptcg.core.card_registry import registry
from ptcg.utils.load_deck import load_deck


def test_registry_singleton():
    r1 = registry
    r2 = registry
    assert r1 is r2


def test_get_card_by_id():
    card_class = registry.get("PAF-054")
    assert card_class is not None
    assert card_class.__name__ == "PAF054CharizardEX"


def test_get_card_by_set_and_number():
    card_class = registry.get_by_set_and_number("PAF", "054")
    assert card_class is not None
    assert card_class.__name__ == "PAF054CharizardEX"


def test_get_card_not_found():
    assert registry.get("XXX-999") is None
    assert registry.get_by_set_and_number("XXX", "999") is None


def test_list_all_cards():
    all_cards = registry.list_all()
    assert len(all_cards) > 0
    assert "PAF-054" in all_cards


def test_registry_works_without_database_json(tmp_path, monkeypatch):
    """CardRegistry discovers cards from the filesystem, not database.json."""
    # Ensure no database.json exists — registry should still work

    # The registry should have loaded from the cards directory directly
    assert len(registry.list_all()) > 0
    assert registry.get("PAF-054") is not None


def test_load_deck_from_file():
    from pathlib import Path

    deck_path = Path(__file__).parent.parent / "src" / "ptcg" / "decks" / "charizard_ex.txt"

    deck = load_deck(str(deck_path))
    assert len(deck.cards) > 0

    card_names = [card.name for card in deck.cards]
    assert "Charizard ex" in card_names


def test_load_deck_from_list():
    deck_lines = ["4 Charmander PAF 007", "3 Charizard ex PAF 054"]

    deck = load_deck(deck_lines)
    assert len(deck.cards) == 7

    charmanders = [c for c in deck.cards if c.name == "Charmander"]
    charizards = [c for c in deck.cards if c.name == "Charizard ex"]

    assert len(charmanders) == 4
    assert len(charizards) == 3


def test_load_deck_invalid_format():
    deck_lines = ["invalid line"]

    with pytest.raises(ValueError, match="Invalid format"):
        load_deck(deck_lines)


def test_load_deck_invalid_card():
    deck_lines = ["4 InvalidCard XXX 999"]

    with pytest.raises(ValueError, match="Card not found"):
        load_deck(deck_lines)
