from ptcg.core.action import AttachEnergyAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardType, EnergyType
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import can_attach_energy, current_all_pokemon


class SVE005BasicPsychicEnergy(EnergyCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SVE"
        self.number = "005"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Psychic Energy"
        self.cardType = CardType.PSYCHIC
        self.energyType = EnergyType.BASIC
        self.provides = [CardType.PSYCHIC]

    def get_actions(self, state):
        if not can_attach_energy(state):
            return []
        return [
            AttachEnergyAction(state.turn, self, pokemon) for pokemon in current_all_pokemon(state)
        ]

    def reduce_action(self, action, state):
        if isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
