from collections import Counter

from ptcg.core.card import EnergyCard, PokemonCard, get_card_info
from ptcg.core.enums import EnergyType, Stage
from ptcg.core.exceptions import InvalidDeckError


class Deck:
    def __init__(self, cards) -> None:
        self.cards = cards

    def validation_errors(self) -> list[str]:
        """Return violations of the standard 60-card deck construction rules.

        Source: Pokemon TCG Rulebook, Deck Building.
        https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/par_rulebook_en.pdf
        """
        errors = []

        if len(self.cards) != 60:
            errors.append(f"A standard deck must contain exactly 60 cards; found {len(self.cards)}")

        if not any(
            isinstance(card, PokemonCard) and card.stage == Stage.BASIC for card in self.cards
        ):
            errors.append("A standard deck must contain at least one Basic Pokemon")

        limited_names = Counter(
            card.name
            for card in self.cards
            if not (
                isinstance(card, EnergyCard) and card.energyType == EnergyType.BASIC
            )
        )
        for name, count in sorted(limited_names.items()):
            if count > 4:
                errors.append(f"{name} has {count} copies; at most 4 cards with one name are allowed")

        return errors

    def validate(self) -> None:
        """Raise ``InvalidDeckError`` when standard construction rules are violated."""
        errors = self.validation_errors()
        if errors:
            raise InvalidDeckError(errors)

    def is_valid(self) -> bool:
        return not self.validation_errors()

    def get_deck_description(self) -> str:
        """Generate a description of all cards in the deck."""
        card_counts = {}
        for card in self.cards:
            card_info = get_card_info(card)
            card_counts[card_info] = card_counts.get(card_info, 0) + 1

        description = []
        for card_info, count in card_counts.items():
            description.append(f"{count}x {card_info}")

        return "\n".join(description)
