from ptcg.core.action import AttackAction, PlayPokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    CardPosition,
    CardType,
    EnergyType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
    SuperType,
)
from ptcg.core.reducer import reduce_attack_action, reduce_play_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_bench,
    current_player,
    move_cards,
    opponent_active,
)


class MEW123Scyther(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Scyther"
        self.set_name = "MEW"
        self.number = "123"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 70
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.GRASS

        # Retreat/Weakness/Resistance
        self.retreat = []
        self.weakness = [CardType.FIRE]
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
                    "name": "Helpful Slash",
                    "damage": 20,
                    "cost": [CardType.GRASS],
                    "text": "Attach a Basic {G} Energy card from your discard pile to 1 of your Benched Pokémon.",
                }
            ),
            Attack(
                {
                    "name": "Slicing Blade",
                    "damage": 70,
                    "cost": [CardType.GRASS, CardType.COLORLESS],
                    "text": "",
                }
            ),
        ]

    def get_actions(self, state):
        """Return list of currently available actions"""
        actions = []

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
            attack_name = action.attack.name

            if attack_name == "Helpful Slash":
                # Attach basic Grass energy from discard to benched Pokémon
                yield from self._helpful_slash_attack(action, state)
            else:
                # Handle other attacks normally
                yield from reduce_attack_action(action, state)

    def _helpful_slash_attack(self, action, state):
        """Helpful Slash: Attach basic Grass energy to benched Pokémon"""
        player = current_player(state)

        # Find basic Grass energy cards in discard pile
        grass_energy = [
            card
            for card in player.discard
            if card.superType == SuperType.ENERGY
            and card.energyType == EnergyType.BASIC
            and CardType.GRASS in card.provides
        ]

        if grass_energy and len(current_bench(state)) > 0:
            # Attach energy to benched Pokémon
            target_pokemon = current_bench(state)[0]

            # Add energy type to Pokémon's energy list
            target_pokemon.energy.append(CardType.GRASS)

            # Move energy from discard to attachment
            move_cards(
                grass_energy[0],
                (player.id, CardPosition.DISCARD),
                (player.id, CardPosition.BENCH_ATTACHMENT, target_pokemon.index),
                state,
            )

        # Execute normal attack damage
        yield from reduce_attack_action(action, state)
