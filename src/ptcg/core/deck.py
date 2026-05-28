from ptcg.core.card import get_card_info


class Deck:
    def __init__(self, cards) -> None:
        self.cards = cards

    def is_valid(self):
        # TODO: check if the deck is valid
        pass

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
