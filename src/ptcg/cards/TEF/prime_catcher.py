from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class TEF157PrimeCatcher(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "157"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Prime Catcher"
        self.cardType = CardType.NONE
        self.text = (
            "Switch in 1 of your opponent's Benched Pokémon to the Active Spot. "
            "If you do, switch your Active Pokémon with 1 of your Benched Pokémon."
        )

    def get_actions(self, state):
        actions = []
        if len(current_bench(state)) >= 1 and len(opponent_bench(state)) >= 1:
            actions.append(UseItemAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            opponent = opponent_player(state)

            # discard self
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            # switch opponent
            tips = "You used Prime Catcher. You should choose 1 of your opponent's benched Pokemon and switch it to active spot."
            actions = choose_card_actions(
                player.id, opponent.id, 1, 1, opponent_bench(state), tips=tips, source=self
            )
            target = yield from reduce_choose_card_actions(actions, state)
            target = target[0]
            move_pokemon(opponent, opponent.active)
            move_pokemon(opponent, target)

            # switch self
            tips = "You used Prime Catcher. You should choose 1 of your benched Pokemon and switch it to active spot."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, current_bench(state), tips=tips, source=self
            )
            target = yield from reduce_choose_card_actions(actions, state)
            target = target[0]
            move_pokemon(player, player.active)
            move_pokemon(player, target)
