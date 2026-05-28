from ptcg.core.action import AttackAction, EvolvePokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import EnergyCard, PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action
from ptcg.utils.utils import check_energy, opponent_active


class TEF137Cinccino(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TEF"
        self.number = "137"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Cinccino"
        self.hp = 110
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Minccino"]
        self.evolved = []

        self.attacks = [
            Attack({"name": "Gentle Slap", "damage": 30, "cost": [CardType.COLORLESS], "text": ""}),
            Attack(
                {
                    "name": "Special Roll",
                    "damage": 0,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS],
                    "text": "This attack does 70 damage for each Special Energy attached to this Pokémon.",
                }
            ),
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    for target in targets:
                        actions.append(AttackAction(state.turn, self, attack, target))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            if action.attack.name == "Special Roll":
                special_energy_count = 0
                for card in self.attachment:
                    if isinstance(card, EnergyCard) and card.energyType == EnergyType.SPECIAL:
                        special_energy_count += 1

                damage = 70 * special_energy_count

                import copy

                modified_attack = copy.copy(action.attack)
                modified_attack.damage = damage
                modified_action = copy.copy(action)
                modified_action.attack = modified_attack

                yield from reduce_attack_action(modified_action, state)
            else:
                yield from reduce_attack_action(action, state)
