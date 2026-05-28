from ptcg.core.ability import PassiveAbility
from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class BRS041Manaphy(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "BRS"
        self.number = "041"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Manaphy"
        self.hp = 70
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack({"name": "Rain Splash", "damage": 20, "cost": [CardType.WATER], "text": ""})
        ]

        self.ability = [
            PassiveAbility(
                {
                    "name": "Wave Veil",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKED,
                    "onceUsedPerTurn": False,
                    "text": "Prevent all damage done to your Benched Pokémon by attacks from your opponent's Pokémon.",
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
            if action.target in opponent_bench(state):
                action.attack.damage = 0

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
            auto_end_turn(state)

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")
