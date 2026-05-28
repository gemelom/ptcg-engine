from ptcg.core.ability import ActiveAbility
from ptcg.core.action import AttackAction, PlayPokemonAction, UseAbilityAction
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
    Stage,
    SuperType,
)
from ptcg.core.reducer import reduce_attack_action, reduce_play_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_player,
    move_cards,
    opponent_active,
    opponent_player,
)


class ASR046RadiantGreninja(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Radiant Greninja"
        self.set_name = "ASR"
        self.number = "046"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 130
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.RADIANT
        self.stage = Stage.BASIC
        self.cardType = CardType.WATER

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = []
        self.prize = 1

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []

        # Attack definition
        self.attacks = [
            Attack(
                {
                    "name": "Moonlight Shuriken",
                    "damage": 0,
                    "cost": [CardType.WATER, CardType.WATER, CardType.COLORLESS],
                    "text": "Discard 2 Energy from this Pokémon. This attack does 90 damage to 2 of your opponent's Pokémon. (Don't apply Weakness and Resistance for Benched Pokémon.)",
                }
            )
        ]

        # Ability definition
        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Concealed Cards",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "You must discard an Energy card from your hand in order to use this Ability. Once during your turn, you may draw 2 cards.",
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

        # Concealed Cards ability - requires energy card in hand
        for ability in self.ability:
            if (
                not self.abilityUsed
                and not player.onceUsedTurn[ability.name]
                and any(
                    card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
                    for card in player.hand
                )
            ):
                actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, UseAbilityAction):
            self._concealed_cards_ability(action, state)
        elif isinstance(action, AttackAction):
            yield from self._moonlight_shuriken_attack(action, state)

    def _concealed_cards_ability(self, action, state):
        """Concealed Cards: Discard Energy from hand to draw 2 cards"""
        player = current_player(state)

        # Find basic energy cards in hand
        energy_cards = [
            card
            for card in player.hand
            if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
        ]

        if energy_cards:
            # Discard 1 energy card
            move_cards(
                energy_cards[0],
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            # Draw 2 cards
            cards_to_draw = min(2, len(player.left))
            if cards_to_draw > 0:
                draw_cards = player.left[:cards_to_draw]
                move_cards(
                    draw_cards,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

        # Mark ability as used
        self.abilityUsed = True
        player.onceUsedTurn[action.ability.name] = True

    def _moonlight_shuriken_attack(self, action, state):
        """Moonlight Shuriken: Discard 2 energy, do 90 damage to 2 opponent Pokémon"""
        current_player(state)
        opponent = opponent_player(state)

        # Discard 2 energy from this Pokémon
        energy_to_discard = min(2, len(self.energy))
        for _ in range(energy_to_discard):
            if self.energy:
                self.energy.pop(0)

        # Choose up to 2 opponent Pokémon to damage
        # For simplicity, we'll target Active and one benched Pokémon if available
        targets = []

        # Add active Pokémon
        if opponent.active:
            targets.append(opponent.active[0])

        # Add one benched Pokémon
        if opponent.bench:
            targets.append(opponent.bench[0])

        # Deal 90 damage to each target
        for target in targets[:2]:
            target.hp -= 90
            if target.hp <= 0:
                # Handle knockout
                pass  # Knockout logic would go here

        yield from reduce_attack_action(action, state)
