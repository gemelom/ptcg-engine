from ptcg.core.action import AttackAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_play_pokemon_action,
    reduce_recoil_damage,
    reduce_retreat_action,
)
from ptcg.utils.utils import check_energy, next_turn, opponent_active


class SVI165Flamigo(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SVI"
        self.number = "165"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Flamigo"
        self.hp = 110
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.prize = 1

        self.energy = []
        self.attachment = []
        self.attacks = [
            Attack(
                {
                    "name": "Flap",
                    "damage": 30,
                    "cost": [CardType.COLORLESS],
                    "text": "",
                }
            ),
            Attack(
                {
                    "name": "Nosedive",
                    "damage": 110,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS],
                    "text": "This Pokémon also does 20 damage to itself.",
                }
            ),
        ]
        self.ability = []

    def get_actions(self, state):
        if self.position != PokemonPosition.ACTIVE:
            return []

        targets = opponent_active(state)
        return [
            AttackAction(state.turn, self, attack, target)
            for attack in self.attacks
            if check_energy(attack.cost, self.energy)
            for target in targets
        ]

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            if action.attack_template == self.attacks[1]:
                yield from reduce_attack_action(action, state, auto_end_turn=False)
                yield from reduce_recoil_damage(self, 20, state)
                next_turn(state)
            else:
                yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
