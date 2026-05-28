from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class PAL188SuperRod(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "188"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Super Rod"
        self.cardType = CardType.NONE
        self.text = "Shuffle up to 3 in any combination of Pokémon and basic Energy cards from your discard pile back into your deck."

    def get_actions(self, state):
        actions = []

        player = current_player(state)
        actions.append(UseItemAction(player.id, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)

            # discard self
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            cardlist = [
                card
                for card in player.discard
                if card.superType == SuperType.ENERGY
                and card.energyType == EnergyType.BASIC
                or card.superType == SuperType.POKEMON
            ]

            tips = "You used Super Rod. You can choose up to 3 in any combination of Pokemon and basic Energy cards from your discard pile back into your deck."
            actions = choose_card_actions(
                player.id, player.id, 0, min(len(cardlist), 3), cardlist, tips=tips, source=self
            )
            targets = yield from reduce_choose_card_actions(actions, state)
            move_cards(
                targets, (player.id, CardPosition.DISCARD), (player.id, CardPosition.LEFT), state
            )
            shuffle_cards(player.left)
