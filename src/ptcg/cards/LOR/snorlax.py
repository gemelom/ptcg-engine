from ptcg.core.ability import PassiveAbility
from ptcg.core.action import AttackAction, EffectAction, EvolvePokemonAction, PlayPokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityTrigger,
    AbilityType,
    CardType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    SpecialCondition,
    Stage,
)
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action
from ptcg.utils.utils import auto_end_turn, check_energy, opponent_active


class LOR143Snorlax(PokemonCard):
    """Snorlax - LOR 143"""

    def __init__(self) -> None:
        super().__init__()
        self.set_name = "LOR"
        self.number = "143"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Snorlax"
        self.hp = 150
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS

        self.retreat = [
            CardType.COLORLESS,
            CardType.COLORLESS,
            CardType.COLORLESS,
            CardType.COLORLESS,
        ]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []
        self.evolveFrom = []
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Thumping Snore",
                    "damage": 180,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS],
                    "text": "This Pokémon is now Asleep. During Pokémon Checkup, flip 2 coins instead of 1. If either of them is tails, this Pokémon is still Asleep.",
                }
            )
        ]

        self.ability = [
            PassiveAbility(
                {
                    "name": "Unfazed Fat",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKED,
                    "onceUsedPerTurn": False,
                    "text": "Prevent all effects of attacks from your opponent's Pokémon done to this Pokémon. (Damage is not an effect.)",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [
                            AttackAction(state.turn, self, attack, target)
                            for target in opponent_active(state)
                        ]
                    )
        return actions

    def use_ability(self, action, state):
        """Prevent all effects of attacks targeting this Pokémon (not damage)."""
        if isinstance(action, EffectAction):
            if action.target == self:
                action.effect.dc = 0
                action.effect.specialCondition = None

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state, auto_end_turn=False)
            # Put self to sleep after attacking
            self.specialCondition = SpecialCondition.ASLEEP
            auto_end_turn(state)
