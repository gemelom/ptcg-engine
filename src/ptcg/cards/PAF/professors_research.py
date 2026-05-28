from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAF087ProfessorsResearch(SupporterCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAF"
        self.number = "087"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Professor's Research"
        self.cardType = CardType.NONE
        self.text = "Discard your hand and draw 7 cards."

    def get_actions(self, state):
        player = current_player(state)
        actions = []

        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)

            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            hand_copy = list(player.hand)
            for card in hand_copy:
                move_cards(
                    card,
                    (player.id, CardPosition.HAND),
                    (player.id, CardPosition.DISCARD),
                    state,
                )

            draw_count = min(7, len(player.left))
            for _ in range(draw_count):
                move_cards(
                    player.left[0],
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

            player.supporterPlayedTurn = True
