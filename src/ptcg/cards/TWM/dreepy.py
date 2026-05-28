from ptcg.core.action import AttackAction, PlayPokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_attack_action, reduce_play_pokemon_action
from ptcg.utils.utils import check_energy, opponent_active


class TWM128Dreepy(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TWM"
        self.number = "128"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Dreepy"
        self.hp = 70
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS]
        self.weakness = []
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack({"name": "Petty Grudge", "damage": 10, "cost": [CardType.PSYCHIC], "text": ""}),
            Attack(
                {
                    "name": "Bite",
                    "damage": 40,
                    "cost": [CardType.FIRE, CardType.PSYCHIC],
                    "text": "",
                }
            ),
        ]

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
