from ptcg.core.action import AttachEnergyAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardType, EnergyType, SpecialCondition
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import can_attach_energy, current_all_pokemon


class PAL193TherapeuticEnergy(EnergyCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "193"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Therapeutic Energy"
        self.cardType = CardType.COLORLESS
        self.energyType = EnergyType.SPECIAL
        self.provides = [CardType.COLORLESS]
        self.text = "As long as this card is attached to a Pokémon, it provides {C} Energy. The Pokémon this card is attached to recovers from being Asleep, Confused, or Paralyzed and can't be affected by those Special Conditions."

    def get_actions(self, state):
        if not can_attach_energy(state):
            return []
        return [
            AttachEnergyAction(state.turn, self, pokemon) for pokemon in current_all_pokemon(state)
        ]

    def reduce_action(self, action, state):
        if isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
            target = action.target
            if hasattr(target, "specialCondition") and target.specialCondition in [
                SpecialCondition.ASLEEP,
                SpecialCondition.CONFUSED,
                SpecialCondition.PARALYZED,
            ]:
                target.specialCondition = SpecialCondition.NONE
