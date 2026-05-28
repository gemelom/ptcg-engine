from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class MEW017Pidgeotto(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "MEW"
        self.number = "017"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Pidgeotto"
        self.hp = 80
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Pidgey"]
        self.evolved = []

        self.attacks = [
            Attack({"name": "Flap", "damage": 20, "cost": [CardType.COLORLESS], "text": ""})
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)
        current_player(state)

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
