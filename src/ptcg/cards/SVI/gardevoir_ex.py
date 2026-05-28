from ptcg.core.ability import PassiveAbility
from ptcg.core.action import AttackAction, EvolvePokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
)
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_player,
    opponent_active,
)


class SVI086Gardevoirex(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Gardevoir ex"
        self.set_name = "SVI"
        self.number = "086"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 310
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.PSYCHIC

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.DARK]
        self.resistance = []
        self.prize = 2

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.evolveFrom = ["Kirlia", "Ralts"]

        # Attack definitions
        self.attacks = [
            Attack(
                {
                    "name": "Miracle Force",
                    "damage": 190,
                    "cost": [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS],
                    "text": "This Pokémon recovers from all Special Conditions.",
                }
            )
        ]

        # Ability definition
        self.ability = [
            PassiveAbility(
                {
                    "name": "Psychic Embrace",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": False,
                    "text": "As often as you like during your turn, you may attach a Basic {P} Energy card from your discard pile to 1 of your {P} Pokémon. If you attached Energy to a Pokémon in this way, put 2 damage counters on that Pokémon. You can't use this Ability on a Pokémon that would be Knocked Out.",
                }
            )
        ]

    def get_actions(self, state):
        """Return list of currently available actions"""
        actions = []
        current_player(state)

        # If in active position, check if can attack
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))

        # Check if can evolve (Stage 2 and have Ralts or Kirlia)
        # if self.stage == Stage.STAGE_2:
        #     # Find Stage 1 or Basic cards to evolve from
        #     evolved_from = check_evolve(self, state)
        #     if evolved_from:
        #         for pokemon in evolved_from:
        #             actions.append(EvolvePokemonAction(state.turn, pokemon, self))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, EvolvePokemonAction):
            # Execute evolution
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)

    def _apply_psychic_embrace(self, state):
        """Psychic Embrace: Attach Psychic energy and add 2 damage counters"""
        # This ability applies when Psychic energy is attached
        # For simplicity, we'll just ensure the energy tracking is maintained
        # The actual damage counter logic would be more complex
        pass
