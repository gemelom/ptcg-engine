from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class PAR160CounterCatcher(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "160"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Counter Catcher"
        self.cardType = CardType.NONE
        self.text = (
            "You can use this card only if you have more Prize cards remaining than your opponet. "
            "Switch in 1 of your opponent's Benched Pokemon to the Active Spot."
        )

    def get_actions(self, state):
        opponent = opponent_player(state)
        player = current_player(state)
        actions = []
        if len(player.prize) > len(opponent.prize) and len(opponent.bench) != 0:
            actions.extend([UseItemAction(state.turn, self)])

        return actions

    def reduce_action(self, action, state):
        player = current_player(state)
        opponent = opponent_player(state)

        if isinstance(action, UseItemAction):
            # discard self
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            tips = (
                "You used Counter Catcher. You should choose 1 of your opponent's "
                "benched Pokemon and switch it with their active Pokemon."
            )
            actions = choose_card_actions(
                player.id, opponent.id, 1, 1, opponent.bench, tips=tips, source=self
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            chosen_card = chosen_card[0]

            if chosen_card in opponent.bench:
                switch_pokemon(chosen_card, opponent.active[0], opponent)
            else:
                raise ValueError(f"Invalid action: {action}")
