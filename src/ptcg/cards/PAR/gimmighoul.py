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


class PAR088Gimmighoul(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Gimmighoul"
        self.set_name = "PAR"
        self.number = "088"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 70
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.DARK]
        self.resistance = [CardType.FIGHTING]
        self.prize = 1

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []

        # Attack definition
        self.attacks = [
            Attack(
                {
                    "name": "Continuous Coin Toss",
                    "damage": 0,
                    "cost": [CardType.COLORLESS],
                    "text": "Flip a coin until you get tails. This attack does 20 damage for each heads.",
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
            yield from self._continuous_coin_toss_attack(action, state)

    def _continuous_coin_toss_attack(self, action, state):
        """Continuous Coin Toss: Flip coin until tails, 20 damage per heads"""
        total_heads = 0

        # Flip coins until tails
        while True:
            result = flip_coin(state)
            if result == Coin.HEAD:
                total_heads += 1
            else:
                break

        # Calculate damage: 20 per heads
        action.attack.damage = 20 * total_heads

        yield from reduce_attack_action(action, state)
