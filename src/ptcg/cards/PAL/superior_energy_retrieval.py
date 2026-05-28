from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class PAL189SuperiorEnergyRetrieval(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "189"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Superior Energy Retrieval"
        self.cardType = CardType.NONE
        self.text = "You can use this card only if you discard 2 other cards from your hand. Put up to 4 Basic Energy cards from your discard pile into your hand."

    def get_actions(self, state):
        """Check if card can be used"""
        player = current_player(state)
        actions = []

        # Can use if have at least 3 cards in hand (self + 2 to discard)
        if len(player.hand) >= 3:
            actions.append(UseItemAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        """Execute effect"""
        if isinstance(action, UseItemAction):
            player = current_player(state)

            # First, discard 2 other cards from hand
            other_cards = [card for card in player.hand if card != self]
            if len(other_cards) >= 2:
                tips = (
                    "You used Superior Energy Retrieval. Choose 2 cards from your hand to discard."
                )
                actions = choose_card_actions(
                    player.id, player.id, 2, 2, other_cards, tips=tips, source=self
                )
                cards_to_discard = yield from reduce_choose_card_actions(actions, state)

                if cards_to_discard and all(card in player.hand for card in cards_to_discard):
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

            # Find basic energy cards in discard pile (excluding those just discarded)
            basic_energy = [
                card
                for card in player.discard
                if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
            ]

            # Let player choose up to 4 basic energy cards
            tips = "You may choose up to 4 Basic Energy cards from your discard pile to add to your hand."
            actions = choose_card_actions(
                player.id,
                player.id,
                0,
                min(len(basic_energy), 4),
                basic_energy,
                tips=tips,
                source=self,
            )
            chosen_cards = yield from reduce_choose_card_actions(actions, state)

            # Move chosen cards to hand
            if chosen_cards and all(card in player.discard for card in chosen_cards):
                move_cards(
                    chosen_cards,
                    (player.id, CardPosition.DISCARD),
                    (player.id, CardPosition.HAND),
                    state,
                )
