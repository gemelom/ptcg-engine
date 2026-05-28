from ptcg.core.ability import PassiveAbility
from ptcg.core.action import AttachEnergyAction, AttackAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_attach_energy_action


class TEF161MistEnergy(EnergyCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "161"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Mist Energy"
        self.cardType = CardType.COLORLESS
        self.energyType = EnergyType.SPECIAL
        self.provides = [CardType.COLORLESS]
        self.text = (
            "As long as this card is attached to a Pokémon, it provides 1 Colorless Energy. "
            "Prevent all effects of attacks used by your opponent's Pokémon done to the Pokémon "
            "this card is attached to. (Existing effects are not removed. Damage is not an effect.)"
        )

        self.ability = [
            PassiveAbility(
                {
                    "name": "",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKING,
                    "text": self.text,
                }
            )
        ]

    def get_actions(self, state):
        from ptcg.utils.utils import can_attach_energy, current_all_pokemon

        if not can_attach_energy(state):
            return []
        return [
            AttachEnergyAction(state.turn, self, pokemon) for pokemon in current_all_pokemon(state)
        ]

    def use_ability(self, action, state):
        if isinstance(action, AttackAction):
            # TODO: Effect
            if hasattr(action.attack, "effectAttack"):
                action.attack.damage = 0

    def reduce_action(self, action, state):
        if isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
