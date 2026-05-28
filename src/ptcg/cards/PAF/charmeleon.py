from ptcg.core.ability import PassiveAbility
from ptcg.core.action import AttackAction, EffectAction, EvolvePokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action
from ptcg.utils.utils import check_energy, opponent_active


class PAF008Charmeleon(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAF"
        self.number = "008"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Charmeleon"
        self.hp = 90
        self.pokemonType = PokemonType.NORMAL
        self.stage = Stage.STAGE_1
        self.cardType = CardType.FIRE
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.WATER]
        self.evolveFrom = ["Charmander"]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Charmander"]
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Combustion",
                    "damage": 50,
                    "cost": [CardType.FIRE, CardType.FIRE],
                    "text": "",
                }
            )
        ]

        self.ability = [
            PassiveAbility(
                {
                    "name": "Flare Veil",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKED,
                    "onceUsedPerTurn": False,
                    "text": "Prevent all effects of attacks used by your opponent's "
                    "Pokémon done to this Pokémon. (Damage is not an effect.)",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    for target in targets:
                        actions.extend([AttackAction(state.turn, self, attack, target)])

        return actions

    def use_ability(self, action, state):
        if isinstance(action, EffectAction):
            if action.target == self:
                action.effect.damage = 0
                action.effect.specialCondition = None

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
