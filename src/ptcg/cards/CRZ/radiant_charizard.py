from ptcg.core.ability import PassiveAbility
from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class CRZ020RadiantCharizard(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "CRZ"
        self.number = "020"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Radiant Charizard"
        self.hp = 160
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.RADIANT
        self.stage = Stage.BASIC
        self.cardType = CardType.FIRE
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.WATER]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.evolveFrom = []
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Combustion Blast",
                    "damage": 250,
                    "cost": [
                        CardType.FIRE,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                    ],
                    "text": "During your next turn, this Pokémon can't use Combustion Blast.",
                }
            )
        ]

        self.useAttackLastTurn = False

        self.ability = [
            PassiveAbility(
                {
                    "name": "Excited Heart",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.OTHER,
                    "onceUsedPerTurn": False,
                    "text": "This Pokémon's attacks cost 1 Colorless Energy less for each Prize card your opponent has taken.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)
        opponent = opponent_player(state)

        num_prizes_taken = 6 - len(opponent.prize)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                adjusted_cost_list = self._attack_cost_after_excited_heart(
                    attack.cost, num_prizes_taken
                )

                if (
                    check_energy(adjusted_cost_list, self.energy)
                    and self.useAttackLastTurn is False
                ):
                    for target in targets:
                        actions.append(AttackAction(state.turn, self, attack, target))

        return actions

    def _attack_cost_after_excited_heart(self, cost, num_prizes_taken):
        adjusted_cost = list(cost)
        for _ in range(num_prizes_taken):
            if CardType.COLORLESS not in adjusted_cost:
                break
            adjusted_cost.remove(CardType.COLORLESS)
        return adjusted_cost

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
            if action.attack.name == "Combustion Blast":
                self.useAttackLastTurn = True

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
