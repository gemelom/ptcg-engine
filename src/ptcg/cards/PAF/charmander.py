from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class PAF007Charmander(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAF"
        self.number = "007"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Charmander"
        self.hp = 70
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
                    "name": "Blazing Destruction",
                    "damage": 0,
                    "cost": [CardType.FIRE],
                    "text": "Discard a Stadium in play.",
                }
            ),
            Attack(
                {
                    "name": "Steady Firebreathing",
                    "damage": 30,
                    "cost": [CardType.FIRE, CardType.FIRE],
                    "text": "",
                }
            ),
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
            if action.attack == self.attacks[0]:
                if len(state.stadium) > 0:
                    old_stadium = state.stadium[0]
                    old_stadium.reduce_action(
                        DiscardStadiumAction(old_stadium.playedFrom, old_stadium), state
                    )
                auto_end_turn(state)

            elif action.attack == self.attacks[1]:
                yield from reduce_attack_action(action, state)
