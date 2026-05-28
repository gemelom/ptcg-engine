# from ptcg.core.action import AttachToolAction, UseToolAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import *

# from ptcg.core.reducer import reduce_attach_tool_action


class SVI165RigidBand(ToolCard):
    def __init__(self):
        super().__init__()
        self.set_name = "SVI"
        self.number = "165"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Rigid Band"
        self.cardType = CardType.NONE
        self.text = "The Pokémon this card is attached to takes 20 less damage from your opponent’s Pokémon (before applying Weakness and Resistance)."

    def get_actions(self, state):
        """Return list of currently available actions"""
        actions = []

        # Can attach if can attach to any Pokémon
        # if can_attach_tool(state, self):
        #     actions.append(AttachToolAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        # if isinstance(action, UseToolAction):
        #     # Attach tool to target Pokémon
        #     yield from reduce_attach_tool_action(action, state)
        # elif isinstance(action, AttachToolAction):
        #     # Tool attachment is passive - just attach
        #     yield from reduce_attach_tool_action(action, state)
