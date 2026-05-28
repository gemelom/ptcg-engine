from ptcg.core.ability import PassiveAbility
from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityTrigger,
    AbilityType,
    CardType,
    Coin,
    PokemonRule,
    PokemonType,
    Stage,
)
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class CRZ111Bidoof(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "CRZ"
        self.number = "111"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Bidoof"
        self.hp = 60
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Hyper Fang",
                    "damage": 30,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS],
                    "text": "Flip a coin. If tails, this attack does nothing.",
                }
            )
        ]

        self.ability = [
            PassiveAbility(
                {
                    "name": "Carefree Countenance",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKED,
                    "onceUsedPerTurn": False,
                    "text": "As long as this Pokémon is on your Bench, "
                    "prevent all damage done to this Pokémon by attacks (both yours and your opponent's).",
                }
            )
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

    def use_ability(self, action, state):
        if isinstance(action, AttackAction):
            if action.target == self:
                action.attack.damage = 0

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            if flip_coin(state) == Coin.HEAD:
                yield from reduce_attack_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")
