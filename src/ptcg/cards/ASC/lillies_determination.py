from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards, shuffle_cards


class ASC192LilliesDetermination(SupporterCard):
    def __init__(self):
        super().__init__()
        self.set_name = "ASC"
        self.number = "192"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Lillie's Determination"
        self.cardType = CardType.NONE
        self.text = (
            "Shuffle your hand into your deck. Then, draw 6 cards. "
            "If you have exactly 6 Prize cards remaining, draw 8 cards instead."
        )

    def get_actions(self, state):
        player = current_player(state)
        if not player.supporterPlayedTurn:
            return [UseSupporterAction(state.turn, self)]
        return []

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)

            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            if player.hand:
                move_cards(
                    player.hand[:],
                    (player.id, CardPosition.HAND),
                    (player.id, CardPosition.LEFT),
                    state,
                )

            shuffle_cards(player.left)

            draw_count = 8 if len(player.prize) == 6 else 6
            draw_count = min(draw_count, len(player.left))
            draw = player.left[:draw_count]
            move_cards(
                draw,
                (player.id, CardPosition.LEFT),
                (player.id, CardPosition.HAND),
                state,
            )

            player.supporterPlayedTurn = True
