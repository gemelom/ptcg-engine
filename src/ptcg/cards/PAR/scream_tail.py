from ptcg.core.action import AttackAction, PlayPokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    CardType,
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
    opponent_player,
)


class PAR086ScreamTail(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Scream Tail"
        self.set_name = "PAR"
        self.number = "086"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 90
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.DARK]
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
                    "name": "Psybolt",
                    "damage": 20,
                    "cost": [CardType.PSYCHIC],
                    "text": "Flip a coin. If heads, the Defending Pokémon is now Asleep.",
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
            if action.attack.name == "Psybolt":
                yield from self._psybolt_attack(action, state)
            else:
                yield from reduce_attack_action(action, state)

    def _psybolt_attack(self, action, state):
        """Psybolt: Flip coin, if heads put opponent to sleep"""
        from ptcg.utils.utils import Coin

        # Flip coin
        result = flip_coin(state)

        # If heads, opponent's active Pokémon is Asleep
        if result == Coin.HEAD:
            opponent = opponent_player(state)
            if opponent.active:
                opponent.active[0].asleep = True

        # Execute normal attack damage
        yield from reduce_attack_action(action, state)
