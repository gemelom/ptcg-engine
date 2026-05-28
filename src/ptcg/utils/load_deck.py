from pathlib import Path
from typing import List, Union

from ptcg.core.card import Card
from ptcg.core.card_registry import registry
from ptcg.core.deck import Deck

PACKAGE_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = Path.cwd()
DECKS_DIR = PACKAGE_ROOT / "decks"


def _resolve_deck_path(deck_source) -> Path:
    """
    Resolve deck file path with intelligent search.

    Search order:
    1. If absolute path or relative path exists, use it directly
    2. Search in src/ptcg/decks/
    3. Search in project root

    For each location, try both with and without .txt extension.

    Args:
        deck_source: Deck file name or path

    Returns:
        Path to the deck file

    Raises:
        FileNotFoundError: If deck file cannot be found
    """
    deck_source = Path(deck_source)

    # If it's already an absolute path, check if it exists
    if deck_source.is_absolute():
        if deck_source.exists():
            return deck_source
        raise FileNotFoundError(f"Deck file not found: {deck_source}")

    # List of paths to search in order
    search_paths = [DECKS_DIR, PROJECT_ROOT]

    # For each search location, try with and without .txt
    for search_dir in search_paths:
        # Try exact filename first
        candidate = search_dir / deck_source
        if candidate.exists():
            return candidate

        # Try with .txt extension if not present
        if not deck_source.suffix:
            candidate_with_txt = candidate.with_suffix(".txt")
            if candidate_with_txt.exists():
                return candidate_with_txt

    # If not found, raise error
    raise FileNotFoundError(
        f"Deck file not found: '{deck_source}'. Searched in: {DECKS_DIR} and {PROJECT_ROOT}"
    )


def load_deck(deck_source: Union[str, Path, List[str]]) -> Deck:
    """
    Load a deck from file or list of lines.

    Args:
        deck_source: Either a file path/name, or a list of deck lines

    Returns:
        Deck object containing the loaded cards

    Raises:
        TypeError: If deck_source is not str, Path, or list
        ValueError: If a card line is invalid or card not found
        FileNotFoundError: If deck file cannot be found
    """
    cards: List[Card] = []

    # Load lines from file or use provided list
    if isinstance(deck_source, (str, Path)):
        deck_path = _resolve_deck_path(str(deck_source))
        with open(deck_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    elif isinstance(deck_source, list):
        lines = deck_source
    else:
        raise TypeError("deck_source must be str, Path, or list")

    # Parse each line
    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Skip section headers like "Pokémon:" or "Trainer:"
        if ":" in line and not line[0].isdigit():
            continue

        parts = line.split()
        if len(parts) < 4:
            raise ValueError(
                f"Line {line_num}: Invalid format. Expected: <count> <card_name> <set> <number>"
            )

        try:
            count = int(parts[0])
        except ValueError:
            raise ValueError(f"Line {line_num}: Invalid count '{parts[0]}'")

        set_name = parts[-2]
        number = parts[-1].zfill(3)

        card_class = registry.get_by_set_and_number(set_name, number)
        if not card_class:
            raise ValueError(f"Line {line_num}: Card not found: {set_name} {number}")

        for _ in range(count):
            cards.append(card_class())

    return Deck(cards)
