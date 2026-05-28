from ptcg.core.ability import PassiveAbility
from ptcg.core.action import AttackAction, EvolvePokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityTrigger,
    AbilityType,
    CardType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
)
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_player,
    opponent_active,
    opponent_player,
)


class OBF141Scizor(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Scizor"
        self.set_name = "OBF"
        self.number = "141"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 140
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.METAL

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.FIRE]
        self.resistance = [CardType.GRASS]
        self.prize = 2

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.evolveFrom = ["Scyther"]

        # Attack definitions
        self.attacks = [
            Attack(
                {
                    "name": "Punishing Scissors",
                    "damage": 10,
                    "cost": [CardType.METAL],
                    "text": "This attack does 50 more damage for each of your opponent’s Pokémon in play that has an Ability.",
                }
            ),
            Attack(
                {
                    "name": "Cut",
                    "damage": 70,
                    "cost": [CardType.METAL, CardType.COLORLESS],
                    "text": "",
                }
            ),
        ]

        # Ability definition
        self.ability = [
            PassiveAbility(
                {
                    "name": "Hyper Cutter",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKING,
                    "onceUsedPerTurn": False,
                    "text": "Your {M} Pokémon's attacks do 20 less damage to your opponent's Active Pokémon (before applying Weakness and Resistance).",
                }
            )
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
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            attack_name = action.attack.name

            if attack_name == "Punishing Scissors":
                # Calculate bonus damage based on opponent's abilities
                yield from self._punishing_scissors_attack(action, state)
            else:
                # Handle other attacks normally
                yield from reduce_attack_action(action, state)

    def _punishing_scissors_attack(self, action, state):
        """Punishing Scissors: +50 damage per opponent's Pokémon with ability"""
        current_player(state)
        opponent = opponent_player(state)

        opponent_pokemon_with_abilities = 0
        for pokemon in opponent.bench:
            if getattr(pokemon, "ability", None):
                opponent_pokemon_with_abilities += 1

        if opponent.active and getattr(opponent.active[0], "ability", None):
            opponent_pokemon_with_abilities += 1

        # Calculate bonus: 50 per ability-bearing Pokémon
        bonus_damage = opponent_pokemon_with_abilities * 50

        # Set attack damage
        action.attack.damage = 10 + bonus_damage

        yield from reduce_attack_action(action, state)
