from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class PAR163EarthenVessel(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "163"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Earthen Vessel"
        self.cardType = CardType.NONE
        self.text = (
            "You can use this card only if you discard another card from your hand. "
            "Search your deck for up to 2 Basic Energy cards, reveal them, and put "
            "them into your hand. Then, shuffle your deck."
        )

    def get_actions(self, state):
        """Check if card can be used"""
        player = current_player(state)
        actions = []

        # Can use if have at least 2 cards in hand (self + 1 to discard)
        if len(player.hand) >= 2:
            actions.append(UseItemAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        """Execute effect"""
        if isinstance(action, UseItemAction):
            player = current_player(state)

            # First, discard 1 other card from hand
            other_cards = [card for card in player.hand if card != self]
            if other_cards:
                tips = "You used Earthen Vessel. Choose 1 card from your hand to discard."
                actions = choose_card_actions(
                    player.id, player.id, 1, 1, other_cards, tips=tips, source=self
                )
                cards_to_discard = yield from reduce_choose_card_actions(actions, state)

                if (
                    cards_to_discard
                    and len(cards_to_discard) == 1
                    and cards_to_discard[0] in player.hand
                ):
                    move_cards(
                        cards_to_discard,
                        (player.id, CardPosition.HAND),
                        (player.id, CardPosition.DISCARD),
                        state,
                    )

            # Discard this card
            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            # Find basic energy cards in deck
            basic_energy = [
                card
                for card in player.left
                if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
            ]

            # Let player choose up to 2 basic energy cards
            tips = "You may choose up to 2 Basic Energy cards from your deck to add to your hand."
            actions = choose_card_actions(
                player.id,
                player.id,
                0,
                min(len(basic_energy), 2),
                basic_energy,
                tips=tips,
                source=self,
            )
            chosen_cards = yield from reduce_choose_card_actions(actions, state)

            # Move chosen cards to hand
            if chosen_cards and all(card in player.left for card in chosen_cards):
                move_cards(
                    chosen_cards,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

            # Shuffle deck
            shuffle_cards(player.left)
