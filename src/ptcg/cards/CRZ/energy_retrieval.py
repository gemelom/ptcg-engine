from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class CRZ127EnergyRetrieval(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "CRZ"
        self.number = "127"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Energy Retrieval"
        self.cardType = CardType.NONE
        self.text = "Put up to 2 basic Energy cards from your discard pile into your hand."

    def get_actions(self, state):
        """Check if card can be used"""
        player = current_player(state)
        actions = []

        # Can use if there are basic energy cards in discard pile
        basic_energy = [
            card
            for card in player.discard
            if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
        ]

        if basic_energy:
            actions.append(UseItemAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        """Execute effect"""
        if isinstance(action, UseItemAction):
            player = current_player(state)

            # Find basic energy cards in discard pile
            basic_energy = [
                card
                for card in player.discard
                if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
            ]

            # Discard this card
            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            # Let player choose up to 2 basic energy cards
            tips = "You used Energy Retrieval. You may choose up to 2 Basic Energy cards from your discard pile."
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
            if chosen_cards and all(card in player.discard for card in chosen_cards):
                move_cards(
                    chosen_cards,
                    (player.id, CardPosition.DISCARD),
                    (player.id, CardPosition.HAND),
                    state,
                )
