from ptcg.core.action import UseToolAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType, Stage
from ptcg.utils.utils import can_attach_tool, current_all_pokemon, current_player, move_cards


class PAL173BraveryCharm(ToolCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "173"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Bravery Charm"
        self.cardType = CardType.NONE
        self.text = "The Basic Pokémon this card is attached to gets +50 HP."
        self.hasAttached = False
        self.attachedTo = None

    def get_actions(self, state):
        if self.hasAttached:
            return []
        return [
            UseToolAction(state.turn, self, card)
            for card in current_all_pokemon(state)
            if can_attach_tool(card) and card.stage == Stage.BASIC
        ]

    def reduce_action(self, action, state):
        if isinstance(action, UseToolAction):
            player = current_player(state)
            target = action.target
            target_position = (
                CardPosition.ACTIVE_ATTACHMENT
                if target.cardPosition == CardPosition.ACTIVE
                else CardPosition.BENCH_ATTACHMENT
            )
            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, target_position, target.index),
                state,
            )
            self.hasAttached = True
            self.attachedTo = [target]
            target.hp += 50
