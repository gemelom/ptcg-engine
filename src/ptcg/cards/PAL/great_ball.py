from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class PAL183GreatBall(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "183"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Great Ball"
        self.cardType = CardType.NONE
        self.text = (
            "Look at the top 7 cards of your deck. You may reveal a Pokémon you find there "
            "and put it into your hand. Shuffle the other cards back into your deck."
        )

    def get_actions(self, state):
        actions = []
        actions.extend([UseItemAction(state.turn, self)])
        return actions

    def reduce_action(self, action, state):
        player = current_player(state)

        if isinstance(action, UseItemAction):
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            top_7_cards = player.left[:7]
            pokemon_cards = [card for card in top_7_cards if card.superType == SuperType.POKEMON]

            tips = "You used Great Ball. You may reveal a Pokémon you find there and put it into your hand."
            actions = choose_card_actions(
                player.id, player.id, 0, 1, pokemon_cards, tips=tips, source=self
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)

            if len(chosen_card) == 1 and all(card in player.left for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )
            elif len(chosen_card) == 0:
                pass
            else:
                raise ValueError(f"Invalid action: {action}")

            shuffle_cards(player.left)
