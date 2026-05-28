"""Deck validation utilities for Pokemon TCG."""

from pathlib import Path


def get_available_decks() -> list[str]:
    """Get list of available deck names from the decks directory.

    Returns:
        Sorted list of deck filenames without the .txt extension.
    """
    decks_dir = Path(__file__).parent.parent / "decks"
    if not decks_dir.exists():
        return []

    deck_files = sorted(decks_dir.glob("*.txt"))
    return [deck.stem for deck in deck_files]


def validate_deck(deck_name: str) -> str:
    """Validate that a deck exists in the decks directory.

    Args:
        deck_name: Name of the deck (without .txt extension).

    Returns:
        The deck name if valid.

    Raises:
        ValueError: If the deck file doesn't exist, with helpful error message
                    listing available decks.
    """
    decks_dir = Path(__file__).parent.parent / "decks"
    deck_path = decks_dir / f"{deck_name}.txt"

    if not deck_path.exists():
        available_decks = get_available_decks()
        decks_str = ", ".join(available_decks)
        raise ValueError(f"Deck '{deck_name}' not found. Available decks: {decks_str}")

    return deck_name
