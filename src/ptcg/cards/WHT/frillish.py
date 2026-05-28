from ptcg.core.action import AttackAction, PlayPokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_attack_action, reduce_play_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_player,
    opponent_active,
)


class WHT044Frillish(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Frillish"
        self.set_name = "WHT"
        self.number = "044"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 80
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.METAL]
        self.resistance = []
        self.prize = 1

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []

        # Attack definitions
        self.attacks = [
            Attack(
                {
                    "name": "Oceanic Gloom",
                    "damage": 20,
                    "cost": [CardType.PSYCHIC],
                    "text": "",
                }
            ),
            Attack(
                {
                    "name": "Slap",
                    "damage": 40,
                    "cost": [CardType.PSYCHIC, CardType.COLORLESS],
                    "text": "",
                }
            ),
        ]

    def get_actions(self, state):
        """Return list of currently available actions"""
        actions = []
        current_player(state)

        # If in active position, check if can attack
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
