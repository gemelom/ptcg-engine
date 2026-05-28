from ptcg.core.action import AttackAction, PlayPokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    CardType,
    Coin,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
)
from ptcg.core.reducer import reduce_attack_action, reduce_play_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    flip_coin,
    opponent_active,
)


class TEF128Dunsparce(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Dunsparce"
        self.set_name = "TEF"
        self.number = "128"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 60
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS

        # Retreat/Weakness/Resistance
        self.retreat = []
        self.weakness = [CardType.FIGHTING]
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
                    "name": "Gnaw",
                    "damage": 10,
                    "cost": [CardType.COLORLESS],
                    "text": "",
                }
            ),
            Attack(
                {
                    "name": "Dig",
                    "damage": 30,
                    "cost": [CardType.COLORLESS],
                    "text": "Flip a coin. If heads, during your opponent's next turn, prevent all damage from and effects of attacks done to this Pokémon.",
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

            if attack_name == "Dig":
                # Handle Dig with coin flip effect
                yield from self._dig_attack(action, state)
            else:
                # Handle other attacks normally
                yield from reduce_attack_action(action, state)

    def _dig_attack(self, action, state):
        """Dig attack: Flip coin for prevention effect"""
        # Flip a coin
        result = flip_coin(state)

        # If heads, set prevention flag
        if result == Coin.HEAD:
            # This would prevent damage/effects on opponent's next turn
            # For simplicity, we'll need to track this in the game state
            pass

        # Execute normal attack damage
        yield from reduce_attack_action(action, state)
