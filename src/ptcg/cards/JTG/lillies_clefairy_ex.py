from ptcg.core.action import AttackAction, PlayPokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_attack_action, reduce_play_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_player,
    move_cards,
    opponent_active,
)


class JTG056LilliesClefairyex(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Lillie's Clefairy ex"
        self.set_name = "JTG"
        self.number = "056"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 170
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.RADIANT
        self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.METAL]
        self.resistance = []
        self.prize = 2

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []

        # Attack definitions
        self.attacks = [
            Attack(
                {
                    "name": "Triple Dive Energy",
                    "damage": 120,
                    "cost": [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS],
                    "text": "Attach 3 Basic {P} Energy cards to this Pokémon. If you do, this attack does 20 more damage for each of them.",
                }
            ),
            Attack(
                {
                    "name": "Magical Shot",
                    "damage": 160,
                    "cost": [
                        CardType.PSYCHIC,
                        CardType.PSYCHIC,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                    ],
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
            if action.attack.name == "Triple Dive Energy":
                yield from self._triple_dive_energy_attack(action, state)
            else:
                yield from reduce_attack_action(action, state)

    def _triple_dive_energy_attack(self, action, state):
        """Triple Dive Energy: Attach 3 Psychic energy, +20 damage each"""
        player = current_player(state)

        # Find Psychic energy cards in hand
        psychic_energy = [
            card
            for card in player.hand
            if card.superType == SuperType.ENERGY
            and card.energyType == EnergyType.BASIC
            and CardType.PSYCHIC in card.provides
        ]

        # Need  attach up to 3 Psychic energy
        energy_to_attach = min(3, len(psychic_energy))

        if energy_to_attach > 0:
            action.attack.damage = 120 + energy_to_attach * 20
            for energy_card in psychic_energy[:energy_to_attach]:
                self.energy.extend(energy_card.provides)
                move_cards(
                    energy_card,
                    (player.id, CardPosition.HAND),
                    (player.id, CardPosition.ACTIVE_ATTACHMENT),
                    state,
                )

        yield from reduce_attack_action(action, state)
