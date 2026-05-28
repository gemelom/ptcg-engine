from ptcg.core.action import DiscardStadiumAction, PutStadiumAction
from ptcg.core.card import StadiumCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, discard_card, move_cards, opponent_player


class ASC210TeamRocketsWatchtower(StadiumCard):
    def __init__(self):
        super().__init__()
        self.set_name = "ASC"
        self.number = "210"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Team Rocket's Watchtower"
        self.cardType = CardType.NONE
        self.text = "Pokémon in play (both yours and your opponent's) have no Abilities."
        self.playedFrom = None

    def get_actions(self, state):
        player = current_player(state)
        if not player.firstTurn and self in player.hand:
            return [PutStadiumAction(player.id, self)]
        return []

    def reduce_action(self, action, state):
        if isinstance(action, PutStadiumAction):
            player = current_player(state)

            if state.stadium:
                for stadium in state.stadium[:]:
                    state.stadium.remove(stadium)
                    discard_card(player, stadium)

            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.STADIUM),
                state,
            )
            self.playedFrom = player.id

        elif isinstance(action, DiscardStadiumAction):
            player = current_player(state)
            opponent = opponent_player(state)

            state.stadium.remove(self)
            if self.playedFrom == player.id:
                discard_card(player, self)
            elif self.playedFrom == opponent.id:
                discard_card(opponent, self)
