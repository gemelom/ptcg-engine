from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import *
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class PAF080Iono(SupporterCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAF"
        self.number = "080"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Iono"
        self.cardType = CardType.NONE
        self.text = (
            "Each player shuffles their hand and puts it on the bottom of their deck. "
            "If either player put any cards on the bottom of their deck in this way, "
            "each player draws a card for each of their remaining Prize cards."
        )

    def get_actions(self, state):
        """Check if card can be used"""
        player = current_player(state)
        actions = []

        # Can use if no supporter played this turn
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        """Execute effect"""
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            opponent = opponent_player(state)

            # discard self
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            # Shuffle player's hand
            if player.hand:
                shuffle_cards(player.hand)
                move_cards(
                    player.hand[:],
                    (player.id, CardPosition.HAND),
                    (player.id, CardPosition.LEFT),
                    state,
                )

            # If either player put any cards from hand on bottom, draw cards
            cards_to_draw = len(player.prize)

            if cards_to_draw > 0:
                draw_cards = player.left[:cards_to_draw]
                move_cards(
                    draw_cards,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

            # Same for opponent
            if opponent.hand:
                shuffle_cards(opponent.hand)
                move_cards(
                    opponent.hand[:],
                    (opponent.id, CardPosition.HAND),
                    (opponent.id, CardPosition.LEFT),
                    state,
                )

            opponent_cards_to_draw = len(opponent.prize)

            if opponent_cards_to_draw > 0:
                draw_cards = opponent.left[:opponent_cards_to_draw]
                move_cards(
                    draw_cards,
                    (opponent.id, CardPosition.LEFT),
                    (opponent.id, CardPosition.HAND),
                    state,
                )

            # Shuffle decks
            shuffle_cards(player.left)
            shuffle_cards(opponent.left)

        # Mark supporter as used
        player.supporterPlayedTurn = True
        opponent.supporterPlayedTurn = True
