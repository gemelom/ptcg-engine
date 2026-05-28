from ptcg.core.ability import PassiveAbility
from ptcg.core.action import *
from ptcg.core.card import ToolCard
from ptcg.core.enums import *
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class MEW165RigidBand(ToolCard):
    """Rigid Band - MEW 165"""

    def __init__(self):
        super().__init__()
        self.set_name = "MEW"
        self.number = "165"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Rigid Band"
        self.cardType = CardType.NONE
        self.text = "The Stage 1 Pokémon this card is attached to takes 30 less damage from attacks from your opponent's Pokémon (after applying Weakness and Resistance)."

        self.ability = [
            PassiveAbility(
                {
                    "name": "Damage Reduction",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKED,
                    "text": "The Stage 1 Pokémon this card is attached to takes 30 less damage from attacks from your opponent's Pokémon (after applying Weakness and Resistance).",
                }
            )
        ]

        self.hasAttached = False
        self.attachedTo = None

    def get_actions(self, state):
        if self.hasAttached:
            return []
        return [
            UseToolAction(state.turn, self, card)
            for card in current_all_pokemon(state)
            if can_attach_tool(card)
        ]

    def use_ability(self, action, state):
        if isinstance(action, AttackAction):
            if self.attachedTo and len(self.attachedTo) > 0:
                pokemon = self.attachedTo[0]
                if pokemon.stage == Stage.STAGE_1:
                    action.attack.damage = max(0, action.attack.damage - 30)

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
