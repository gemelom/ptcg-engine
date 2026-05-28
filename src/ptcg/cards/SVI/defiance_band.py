from ptcg.core.ability import PassiveAbility
from ptcg.core.action import *
from ptcg.core.card import ToolCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardPosition, CardType
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class SVI169DefianceBand(ToolCard):
    def __init__(self):
        super().__init__()
        self.set_name = "SVI"
        self.number = "169"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Defiance Band"
        self.cardType = CardType.NONE
        self.text = ""
        self.ability = [
            PassiveAbility(
                {
                    "name": "",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKING,
                    "text": "If you have more Prize cards remaining than your opponent, the attacks of the Pokémon this card "
                    "is attached to do 30 more damage to your opponent's Active Pokémon (before applying Weakness "
                    "and Resistance).",
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
            player = current_player(state)
            opponent = opponent_player(state)

            if len(player.prize) > len(opponent.prize):
                action.attack.damage += 30

    def reduce_action(self, action, state):
        player = current_player(state)

        if isinstance(action, UseToolAction):
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
