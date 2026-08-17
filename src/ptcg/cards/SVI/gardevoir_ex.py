from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    EvolvePokemonAction,
    UseAbilityAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardPosition,
    CardType,
    EnergyType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    SpecialCondition,
    Stage,
    SuperType,
)
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_evolve_pokemon_action,
)
from ptcg.utils.utils import (
    check_energy,
    current_all_pokemon,
    current_player,
    move_cards,
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
            ActiveAbility(
                {
                    "name": "Psychic Embrace",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": False,
                    "text": "As often as you like during your turn, you may attach a Basic {P} Energy card from your discard pile to 1 of your {P} Pokémon. If you attached Energy to a Pokémon in this way, put 2 damage counters on that Pokémon. You can't use this Ability on a Pokémon that would be Knocked Out.",
                }
            )
        ]

    def get_actions(self, state):
        """Return list of currently available actions"""
        actions = []
        player = current_player(state)

        # If in active position, check if can attack
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))

        if self._psychic_energy_in_discard(player) and self._psychic_embrace_targets(state):
            actions.append(UseAbilityAction(state.turn, self, self.ability[0]))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, EvolvePokemonAction):
            # Execute evolution
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            self.specialCondition = SpecialCondition.NONE
            yield from reduce_attack_action(action, state)
        elif isinstance(action, UseAbilityAction):
            yield from self._apply_psychic_embrace(state)

    def _apply_psychic_embrace(self, state):
        """Psychic Embrace: Attach Psychic energy and add 2 damage counters"""
        player = current_player(state)
        energy_cards = self._psychic_energy_in_discard(player)
        energy_actions = choose_card_actions(
            player.id,
            player.id,
            1,
            1,
            energy_cards,
            tips="Choose a Basic Psychic Energy from your discard pile.",
            source=self,
        )
        chosen_energy = yield from reduce_choose_card_actions(energy_actions, state)

        targets = self._psychic_embrace_targets(state)
        target_actions = choose_card_actions(
            player.id,
            player.id,
            1,
            1,
            targets,
            indexed=True,
            tips="Choose a Psychic Pokémon that will not be Knocked Out by 2 damage counters.",
            source=self,
        )
        chosen_target = yield from reduce_choose_card_actions(target_actions, state)
        energy = chosen_energy[0]
        target = chosen_target[0]
        target_position = (
            CardPosition.ACTIVE_ATTACHMENT
            if target.position == PokemonPosition.ACTIVE
            else CardPosition.BENCH_ATTACHMENT
        )
        move_cards(
            energy,
            (player.id, CardPosition.DISCARD),
            (player.id, target_position, target.index),
            state,
        )
        target.energy.extend(energy.provides)
        target.hp -= 20

    @staticmethod
    def _psychic_energy_in_discard(player):
        return [
            card
            for card in player.discard
            if card.superType == SuperType.ENERGY
            and card.energyType == EnergyType.BASIC
            and CardType.PSYCHIC in card.provides
        ]

    @staticmethod
    def _psychic_embrace_targets(state):
        return [
            pokemon
            for pokemon in current_all_pokemon(state)
            if pokemon.cardType == CardType.PSYCHIC and pokemon.hp > 20
        ]
