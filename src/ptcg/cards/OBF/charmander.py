from ptcg.core.action import AttackAction, PlayPokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class OBF026Charmander(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "OBF"
        self.number = "026"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Charmander"
        self.hp = 60
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.FIRE
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.WATER]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Heat Tackle",
                    "damage": 30,
                    "cost": [CardType.FIRE],
                    "text": "This Pokémon also does 10 damage to itself.",
                }
            )
        ]

        self.ability = []

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)

            damage_self_attack = Attack({"damage": 10})
            yield from reduce_attack_action(
                AttackAction(state.turn, self, damage_self_attack, self), state
            )
