from ptcg.core.action import UseToolAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType, PokemonRule
from ptcg.utils.utils import can_attach_tool, current_all_pokemon, current_player, move_cards


class PAR166LuxuriousCape(ToolCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "166"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Luxurious Cape"
        self.cardType = CardType.NONE
        self.text = (
            "If the Pokémon this card is attached to doesn't have a Rule Box, it gets +100 HP."
        )
        self.hasAttached = False
        self.attachedTo = None

    def get_actions(self, state):
        if self.hasAttached:
            return []
        return [
            UseToolAction(state.turn, self, card)
            for card in current_all_pokemon(state)
            if can_attach_tool(card) and card.pokemonRule == PokemonRule.NONE
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
            target.hp += 100
