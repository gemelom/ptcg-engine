from ptcg.core.ability import PassiveAbility
from ptcg.core.action import RetreatAction, UseToolAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardPosition, CardType
from ptcg.utils.utils import (
    can_attach_tool,
    current_active,
    current_all_pokemon,
    current_player,
    move_cards,
)


class TEF159RescueBoard(ToolCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "159"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Rescue Board"
        self.cardType = CardType.NONE
        self.text = (
            "The Retreat Cost of the Pokémon this card is attached to is {C} less. "
            "If that Pokémon's remaining HP is 30 or less, it has no Retreat Cost."
        )
        self.ability = [
            PassiveAbility(
                {
                    "name": "Rescue Board",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.RETREAT,
                    "text": self.text,
                }
            )
        ]
        self.hasAttached = False
        self.attachedTo = None
        self._base_retreat_len = 0

    def get_actions(self, state):
        if self.hasAttached:
            return []
        return [
            UseToolAction(state.turn, self, card)
            for card in current_all_pokemon(state)
            if can_attach_tool(card)
        ]

    def use_ability(self, action, state):
        if not isinstance(action, RetreatAction) or not self.attachedTo:
            return
        active = current_active(state)
        if not active or active[0] is not self.attachedTo[0]:
            return
        pokemon = active[0]
        if pokemon.hp <= 30:
            target_len = 0
        else:
            target_len = max(0, self._base_retreat_len - 1)
        pokemon.retreat = [CardType.COLORLESS] * target_len

    def reduce_action(self, action, state):
        if isinstance(action, UseToolAction):
            player = current_player(state)
            target = action.target
            self._base_retreat_len = len(target.retreat)
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
