from ptcg.core.action import AttachEnergyAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardType, EnergyType
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import can_attach_energy, current_all_pokemon


class LOR171GiftEnergy(EnergyCard):
    def __init__(self):
        super().__init__()
        self.set_name = "LOR"
        self.number = "171"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Gift Energy"
        self.cardType = CardType.COLORLESS
        self.energyType = EnergyType.SPECIAL
        self.provides = [CardType.COLORLESS]
        self.text = (
            "As long as this card is attached to a Pokémon, it provides {C} Energy. "
            "If the Pokémon this card is attached to is Knocked Out by damage from an attack "
            "from your opponent's Pokémon, draw a card."
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
