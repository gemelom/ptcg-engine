from typing import TYPE_CHECKING, cast

from ptcg.core.action import AttachEnergyAction, choose_card_actions
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardPosition, CardType, EnergyType
from ptcg.core.reducer import reduce_attach_energy_action, reduce_choose_card_actions
from ptcg.utils.utils import (
    can_attach_energy,
    current_all_pokemon,
    current_player,
    switch_pokemon,
)

if TYPE_CHECKING:
    from ptcg.core.card import PokemonCard
    from ptcg.core.state import State


class PAL190JetEnergy(EnergyCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "190"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Jet Energy"
        self.cardType = CardType.COLORLESS
        self.energyType = EnergyType.SPECIAL
        self.provides = [CardType.COLORLESS]
        self.text = (
            "As long as this card is attached to a Pokémon, it provides {C} Energy. "
            "When you attach this card from your hand to your Active Pokémon, "
            "switch that Pokémon with 1 of your Benched Pokémon."
        )

    def get_actions(self, state: "State"):
        if not can_attach_energy(state):
            return []
        return [
            AttachEnergyAction(state.turn, self, pokemon) for pokemon in current_all_pokemon(state)
        ]

    def reduce_action(self, action: AttachEnergyAction, state: "State"):
        if isinstance(action, AttachEnergyAction):
            player = current_player(state)
            target = cast("PokemonCard", action.target)
            was_active = target.cardPosition == CardPosition.ACTIVE

            reduce_attach_energy_action(action, state)

            if was_active and len(player.bench) > 0:
                switch_tips = "You attached Jet Energy to your Active Pokémon. Choose 1 of your Benched Pokémon to switch with your Active Pokémon."
                switch_actions = choose_card_actions(
                    player.id, player.id, 1, 1, player.bench, tips=switch_tips
                )
                bench_target = yield from reduce_choose_card_actions(switch_actions, state)
                bench_target = bench_target[0]

                switch_pokemon(target, bench_target, player)
