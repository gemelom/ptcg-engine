from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class OBF189LetterofEncouragement(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "OBF"
        self.number = "189"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Letter of Encouragement"
        self.cardType = CardType.NONE
        self.text = (
            "You can use this card only if any of your Pokémon were Knocked Out during "
            "your opponent’s last turn. Search your deck for up to 3 Basic Energy cards, "
            "reveal them, and put them into your hand. Then, shuffle your deck."
        )

    def get_actions(self, state):
        """Return list of currently available actions"""
        player = current_player(state)

        if player.hasPokemonDead:
            return [UseItemAction(player.id, self)]
        return []

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, UseItemAction):
            player = current_player(state)

            energy_cards = [
                card
                for card in player.left
                if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
            ]
            max_energy = min(len(energy_cards), 3)

            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            if energy_cards:
                tips = (
                    "You used Letter of Encouragement. You may choose up to 3 Basic "
                    "Energy cards from your deck to add to your hand."
                )
                actions = choose_card_actions(
                    player.id,
                    player.id,
                    0,
                    max_energy,
                    energy_cards,
                    tips=tips,
                    source=self,
                )
                chosen_energy = yield from reduce_choose_card_actions(actions, state)

                # Move chosen energy to hand
                if chosen_energy and all(card in player.left for card in chosen_energy):
                    move_cards(
                        chosen_energy,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.HAND),
                        state,
                    )

            shuffle_cards(player.left)
