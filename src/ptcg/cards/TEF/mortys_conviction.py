from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class TEF155MortysConviction(SupporterCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "155"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Morty's Conviction"
        self.cardType = CardType.NONE
        self.text = "You can use this card only if you discard another card from your hand. Draw a card for each of your opponent's Benched Pokémon."

    def get_actions(self, state):
        """Check if card can be used"""
        player = current_player(state)
        opponent = opponent_player(state)

        actions = []

        # Can use if no supporter played this turn
        if not player.supporterPlayedTurn:
            # Can use if have at least 2 cards in hand (self + 1 to discard)
            if len(player.hand) >= 2:
                # Can use only if opponent has benched Pokémon
                if len(opponent.bench) >= 1:
                    actions.append(UseSupporterAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        """Execute effect"""
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            opponent = opponent_player(state)

            # Discard 1 other card from hand
            other_cards = [card for card in player.hand if card != self]
            if other_cards:
                tips = "You used Morty's Conviction. Choose 1 card from your hand to discard."
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

            # Draw 1 card for each benched Pokémon
            if opponent.bench:
                cards_to_draw = min(len(opponent.bench), len(player.left))
                for _ in range(cards_to_draw):
                    if player.left:
                        card_to_draw = player.left[0]
                        move_cards(
                            [card_to_draw],
                            (player.id, CardPosition.LEFT),
                            (player.id, CardPosition.HAND),
                            state,
                        )

        # Mark supporter as used
        player.supporterPlayedTurn = True
