from ptcg.core.ability import ActiveAbility
from ptcg.core.action import AttackAction, PlayPokemonAction, UseAbilityAction, choose_card_actions
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
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_play_pokemon_action,
)
from ptcg.utils.utils import (
    check_energy,
    current_player,
    move_cards,
    opponent_active,
)


class PAL264SquawkabillyEX(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAL"
        self.number = "264"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Squawkabilly ex"
        self.hp = 160
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.prize = 2

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Motivate",
                    "damage": 20,
                    "cost": [CardType.COLORLESS],
                    "text": "Attach up to 2 Basic Energy cards from your discard pile to 1 of your Benched Pokémon.",
                }
            )
        ]

        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Squawk and Seize",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your first turn, you may discard your hand and draw 6 cards. You can't use more than 1 Squawk and Seize Ability during your turn.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)
        player = current_player(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        # Squawk and Seize ability - only on first turn
        for ability in self.ability:
            if (
                not self.abilityUsed
                and not player.onceUsedTurn[ability.name]
                and player.firstTurn  # Only during first turn
            ):
                actions.extend([UseAbilityAction(state.turn, self, ability)])

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            # Motivate attack - attach energy from discard to bench
            yield from self._motivate_attack(action, state)

        elif isinstance(action, UseAbilityAction):
            # Squawk and Seize - discard hand and draw 6 cards
            self._squawk_and_seize_ability(action, state)

    def _motivate_attack(self, action, state):
        """
        Motivate attack: Attach up to 2 Basic Energy cards from discard pile to 1 Benched Pokémon.
        """
        player = current_player(state)

        # Find basic energy cards in discard pile
        basic_energy_cards = [
            card
            for card in player.discard
            if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
        ]

        if basic_energy_cards and len(player.bench) > 0:
            # First, choose up to 2 basic energy cards from discard
            tips = "You used Motivate. You may choose up to 2 Basic Energy cards from your discard pile."
            actions = choose_card_actions(
                player.id,
                player.id,
                0,
                min(len(basic_energy_cards), 2),
                basic_energy_cards,
                tips=tips,
                source=self,
            )

            chosen_energies = yield from reduce_choose_card_actions(actions, state)

            if chosen_energies:
                # Then choose 1 Benched Pokémon to attach them to
                tips = "Choose 1 of your Benched Pokémon to attach the selected energy cards to."
                actions = choose_card_actions(
                    player.id, player.id, 1, 1, player.bench, tips=tips, source=self
                )

                target_pokemon = yield from reduce_choose_card_actions(actions, state)
                target_pokemon = target_pokemon[0]

                # Attach the chosen energy cards to the target Pokémon
                for energy_card in chosen_energies:
                    # Add energy type to Pokémon's energy list
                    provides = energy_card.provides
                    target_pokemon.energy.extend(provides)

                    # Move energy card from discard to attachment
                    move_cards(
                        energy_card,
                        (player.id, CardPosition.DISCARD),
                        (player.id, CardPosition.BENCH_ATTACHMENT, target_pokemon.index),
                        state,
                    )

        # Execute normal attack damage
        yield from reduce_attack_action(action, state)

    def _squawk_and_seize_ability(self, action, state):
        """
        Squawk and Seize ability: Discard hand and draw 6 cards (first turn only).
        """
        player = current_player(state)

        # Discard entire hand
        if player.hand:
            move_cards(
                player.hand[:],  # Copy the list to avoid modification during iteration
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

        # Draw 6 cards
        cards_to_draw = min(6, len(player.left))
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
