from ptcg.core.action import AttachEnergyAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardType, EnergyType
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import can_attach_energy, current_all_pokemon


class BRS151DoubleTurboEnergy(EnergyCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "BRS"
        self.number = "151"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Double Turbo Energy"
        self.cardType = CardType.COLORLESS
        self.energyType = EnergyType.SPECIAL
        self.provides = [CardType.COLORLESS, CardType.COLORLESS]
        self.text = (
            "As long as this card is attached to a Pokémon, it provides 2 Colorless Energy. "
            "The attacks of the Pokémon this card is attached to do 20 less damage to your "
            "opponent's Pokémon (before applying Weakness and Resistance)."
        )

    def get_actions(self, state):
        if not can_attach_energy(state):
            return []
        return [
            AttachEnergyAction(state.turn, self, pokemon) for pokemon in current_all_pokemon(state)
        ]

    def reduce_action(self, action, state):
        if isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
