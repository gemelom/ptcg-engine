from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class TEF145CiphermaniacsCodebreaking(SupporterCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "145"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Ciphermaniac's Codebreaking"
        self.cardType = CardType.NONE
        self.text = "Search your deck for 2 cards, shuffle your deck, then put those cards on top of it in any order."

    def get_actions(self, state):
        """Check if card can be used"""
        player = current_player(state)
        actions = []

        # Can use if no supporter played this turn and not first turn
        if not player.supporterPlayedTurn and not player.firstTurn:
            # Can use if at least 2 cards in deck (to search 2)
            if len(player.left) >= 2:
                actions.append(UseSupporterAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        """Execute effect"""
        if isinstance(action, UseSupporterAction):
            player = current_player(state)

            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            # Step 1: Player chooses 2 cards from deck
            tips = "Ciphermaniac's Codebreaking: choose 2 cards from your deck to put on top."
            actions = choose_card_actions(
                player.id, player.id, 2, 2, player.left[:], tips=tips, source=self
            )
            chosen = yield from reduce_choose_card_actions(actions, state)

            # Step 2: Remove chosen cards from deck, then shuffle remaining
            for card in chosen:
                player.left.remove(card)
            shuffle_cards(player.left)

            # Step 3: Player chooses which card goes on top (drawn first)
            tips = "Choose which card to place on top of your deck (it will be drawn first)."
            order_actions = choose_card_actions(
                player.id, player.id, 1, 1, chosen, tips=tips, source=self
            )
            top_card_list = yield from reduce_choose_card_actions(order_actions, state)
            top_card = top_card_list[0]
            second_card = next(c for c in chosen if c is not top_card)

            # Step 4: Insert onto top of deck (index 0 = drawn first)
            player.left.insert(0, second_card)
            player.left.insert(0, top_card)
            for idx, card in enumerate(player.left):
                card.cardPosition = CardPosition.LEFT
                card.index = idx + 1

        player.supporterPlayedTurn = True
