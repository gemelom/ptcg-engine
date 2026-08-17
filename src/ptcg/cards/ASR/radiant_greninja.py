import copy

from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    PlayPokemonAction,
    UseAbilityAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import EnergyCard, PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardPosition,
    CardType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
    SuperType,
)
from ptcg.core.reducer import (
    reduce_attack_damage,
    reduce_choose_card_actions,
    reduce_play_pokemon_action,
)
from ptcg.utils.utils import (
    check_energy,
    current_player,
    move_cards,
    next_turn,
    opponent_active,
    opponent_all_pokemon,
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
            attached_energy = [
                card for card in self.attachment if isinstance(card, EnergyCard)
            ]
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy) and len(attached_energy) >= 2:
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))

        # Concealed Cards ability - requires energy card in hand
        for ability in self.ability:
            if (
                not self.abilityUsed
                and not player.onceUsedTurn[ability.name]
                and any(card.superType == SuperType.ENERGY for card in player.hand)
            ):
                actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, UseAbilityAction):
            yield from self._concealed_cards_ability(action, state)
        elif isinstance(action, AttackAction):
            yield from self._moonlight_shuriken_attack(action, state)

    def _concealed_cards_ability(self, action, state):
        """Concealed Cards: Discard Energy from hand to draw 2 cards"""
        player = current_player(state)

        # Concealed Cards can discard any Energy card, including Special Energy.
        energy_cards = [
            card
            for card in player.hand
            if card.superType == SuperType.ENERGY
        ]

        if energy_cards:
            actions = choose_card_actions(
                player.id,
                player.id,
                1,
                1,
                energy_cards,
                tips="Choose an Energy card from your hand to discard for Concealed Cards.",
                source=self,
            )
            chosen_energy = yield from reduce_choose_card_actions(actions, state)

            move_cards(
                chosen_energy[0],
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
        player = current_player(state)
        opponent = opponent_player(state)

        attached_energy = [card for card in self.attachment if isinstance(card, EnergyCard)]
        energy_actions = choose_card_actions(
            player.id,
            player.id,
            2,
            2,
            attached_energy,
            tips="Choose 2 Energy attached to Radiant Greninja to discard.",
            source=self,
        )
        chosen_energy = yield from reduce_choose_card_actions(energy_actions, state)
        source_position = (
            CardPosition.ACTIVE_ATTACHMENT
            if self.position == PokemonPosition.ACTIVE
            else CardPosition.BENCH_ATTACHMENT
        )
        for energy_card in chosen_energy:
            move_cards(
                energy_card,
                (player.id, source_position, self.index),
                (player.id, CardPosition.DISCARD),
                state,
            )
            for provided_type in energy_card.provides:
                if provided_type in self.energy:
                    self.energy.remove(provided_type)

        candidates = opponent_all_pokemon(state)
        target_count = min(2, len(candidates))
        target_actions = choose_card_actions(
            player.id,
            opponent.id,
            target_count,
            target_count,
            candidates,
            indexed=True,
            tips="Choose 2 of your opponent's Pokémon for Moonlight Shuriken.",
            source=self,
        )
        targets = yield from reduce_choose_card_actions(target_actions, state)

        # Resolve originally Benched targets first so an Active knockout and
        # forced promotion cannot change whether Weakness/Resistance applies.
        selected_targets = [
            (target, target.position == PokemonPosition.ACTIVE) for target in targets
        ]
        for target, was_active in sorted(selected_targets, key=lambda item: item[1]):
            spread_attack = copy.copy(action.attack)
            spread_attack.damage = 90
            spread_action = AttackAction(state.turn, self, spread_attack, target)
            yield from reduce_attack_damage(
                spread_action,
                state,
                apply_weakness_resistance=was_active,
            )

        next_turn(state)
