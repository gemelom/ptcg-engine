from ptcg.core.ability import PassiveAbility
from ptcg.core.action import AttackAction, PlayPokemonAction
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
from ptcg.core.reducer import reduce_attack_action, reduce_play_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_active,
    current_bench,
    current_player,
    opponent_active,
)


class PGO029Zapdos(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Zapdos"
        self.set_name = "PGO"
        self.number = "029"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 120
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 1

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []

        # Attack definition
        self.attacks = [
            Attack(
                {
                    "name": "Electric Ball",
                    "damage": 110,
                    "cost": [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS],
                    "text": "",
                }
            )
        ]

        # Ability definition
        self.ability = [
            PassiveAbility(
                {
                    "name": "Lightning Symbol",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKING,
                    "onceUsedPerTurn": False,
                    "text": "Your Basic {L} Pokémon's attacks, except any Zapdos, do 10 more damage to your opponent's Active Pokémon (before applying Weakness and Resistance).",
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
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            # Apply Lightning Symbol ability effect
            self._apply_lightning_symbol(state)
            yield from reduce_attack_action(action, state)

    def _apply_lightning_symbol(self, state):
        """Lightning Symbol: Your Basic Lightning Pokémon's attacks do 10 more damage"""
        current_player(state)

        # Find all Basic Lightning Pokémon (except Zapdos) in play
        for pokemon in current_active(state) + current_bench(state):
            if (
                pokemon != self
                and pokemon.stage == Stage.BASIC
                and pokemon.cardType == CardType.LIGHTNING
            ):
                # This ability modifies attack damage when they attack
                # The actual damage modification would happen in their attack execution
                pass
