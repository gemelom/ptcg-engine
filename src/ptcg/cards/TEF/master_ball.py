from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class TEF153MasterBall(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "153"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Master Ball"
        self.cardType = CardType.NONE
        self.text = (
            "You can use this card only if you discard another card from your hand. "
            "Search your deck for a Pokémon, reveal it, and put it into your hand. Then, shuffle your deck."
        )

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if len(player.hand) >= 2:
            actions.append(UseItemAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)

            getCards = [card for card in player.left if card.superType == SuperType.POKEMON]

            move_cards(
                action.source,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            discardCards = player.hand

            tips = "You used Master Ball. You should choose 1 card in your hand to discard."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, discardCards, tips=tips, source=self
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.hand for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.HAND),
                    (player.id, CardPosition.DISCARD),
                    state,
                )
            else:
                raise ValueError(f"Invalid action: {action}")

            tips = "You used Master Ball. You can choose up to 1 Pokemon from your deck and put it into your hand."
            actions = choose_card_actions(
                player.id, player.id, 0, 1, getCards, tips=tips, source=self
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.left for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )
            else:
                raise ValueError(f"Invalid action: {action}")

            shuffle_cards(player.left)
