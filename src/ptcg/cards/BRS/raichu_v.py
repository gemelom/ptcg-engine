from ptcg.core.action import AttackAction, PlayPokemonAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
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
    current_all_pokemon,
    current_player,
    move_cards,
    opponent_active,
    shuffle_cards,
)


class BRS158RaichuV(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "BRS"
        self.number = "158"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Raichu V"
        self.hp = 200
        self.pokemonType = PokemonType.V
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 2

        self.energy = []
        self.attachment = []
        self.fastChargeUsed = False  # 添加标志以跟踪Fast Charge是否已使用

        self.attacks = [
            Attack(
                {
                    "name": "Fast Charge",
                    "damage": 0,
                    "cost": [CardType.LIGHTNING],
                    "text": "If you go first, you can use this attack during your first turn. Search your deck for a [L] Energy card and attach it to this Pokémon. Then, shuffle your deck.",
                }
            ),
            Attack(
                {
                    "name": "Dynamic Spark",
                    "damage": 60,
                    "cost": [CardType.LIGHTNING, CardType.LIGHTNING],
                    "text": "You may discard any amount of [L] Energy from your Pokémon. This attack does 60 damage for each card you discarded in this way.",
                }
            ),
        ]

        self.ability = []

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)
        player = current_player(state)

        if self.position == PokemonPosition.ACTIVE:
            for i, attack in enumerate(self.attacks):
                if check_energy(attack.cost, self.energy):
                    # Special case for Fast Charge - can use on first turn if going first
                    if i == 0 and attack.name == "Fast Charge":
                        # Check if Fast Charge has already been used this turn
                        if self.fastChargeUsed:
                            continue
                        # Check if it's first turn (regardless of which player)
                        if player.firstTurn:
                            actions.extend(
                                [
                                    AttackAction(state.turn, self, attack, target)
                                    for target in targets
                                ]
                            )
                        elif not player.firstTurn:
                            # Can use normally after first turn
                            actions.extend(
                                [
                                    AttackAction(state.turn, self, attack, target)
                                    for target in targets
                                ]
                            )
                    else:
                        # Regular attack check - not on first turn
                        if not player.firstTurn:
                            actions.extend(
                                [
                                    AttackAction(state.turn, self, attack, target)
                                    for target in targets
                                ]
                            )

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            if action.attack == self.attacks[0]:
                # Fast Charge - search for lightning energy and attach
                self.fastChargeUsed = True  # 标记Fast Charge已使用
                yield from self._fast_charge_attack(action, state)
            elif action.attack == self.attacks[1]:
                # Dynamic Spark - discard lightning energy for damage
                yield from self._dynamic_spark_attack(action, state)
            else:
                raise ValueError(f"Invalid attack: {action.attack}")

    def reset_turn_stats(self):
        """Reset stats at the beginning of each turn"""
        self.fastChargeUsed = False

    def _fast_charge_attack(self, action, state):
        """
        Fast Charge attack: Search deck for Lightning Energy card and attach it to this Pokémon.
        """
        player = current_player(state)

        # Execute attack with 0 damage (as specified in card definition)
        # This ensures the attack is properly processed even on first turn
        yield from reduce_attack_action(action, state, auto_end_turn=False)

        # Search for Lightning Energy cards in deck
        lightning_energy_cards = [
            card
            for card in player.left
            if card.superType == SuperType.ENERGY
            and card.energyType == EnergyType.BASIC
            and CardType.LIGHTNING in card.provides
        ]

        if lightning_energy_cards:
            tips = "You used Fast Charge. You may search your deck for a Lightning Energy card and attach it to this Pokémon."
            actions = choose_card_actions(
                player.id, player.id, 0, 1, lightning_energy_cards, tips=tips, source=self
            )

            chosen_card = yield from reduce_choose_card_actions(actions, state)

            if chosen_card and all(card in player.left for card in chosen_card):
                # Attach the energy to this Pokémon
                energy_card = chosen_card[0]
                provides = energy_card.provides
                self.energy.extend(provides)

                # Move the energy card to attachment
                if self.cardPosition == CardPosition.ACTIVE:
                    move_cards(
                        energy_card,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.ACTIVE_ATTACHMENT, self.index),
                        state,
                    )
                else:
                    move_cards(
                        energy_card,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.BENCH_ATTACHMENT, self.index),
                        state,
                    )

        # Shuffle deck
        shuffle_cards(player.left)

        # End turn appropriately based on whether it's the first turn
        if player.firstTurn:
            from ptcg.utils.utils import auto_end_turn

            auto_end_turn(state)
        else:
            from ptcg.utils.utils import next_turn

            next_turn(state)

    def _dynamic_spark_attack(self, action, state):
        """
        Dynamic Spark attack: Discard Lightning Energy from your Pokémon to increase damage.
        """
        player = current_player(state)

        # Collect all Lightning Energy from all player's Pokémon
        lightning_energy_cards = []
        for pokemon in current_all_pokemon(state):
            for energy_card in pokemon.attachment:
                if hasattr(energy_card, "provides") and CardType.LIGHTNING in energy_card.provides:
                    lightning_energy_cards.append(energy_card)

        if lightning_energy_cards:
            tips = "You used Dynamic Spark. You may discard any amount of Lightning Energy from your Pokémon. This attack does 60 damage for each card you discarded."
            actions = choose_card_actions(
                player.id,
                player.id,
                0,
                len(lightning_energy_cards),
                lightning_energy_cards,
                tips=tips,
                source=self,
            )

            chosen_cards = yield from reduce_choose_card_actions(actions, state)

            if chosen_cards:
                # Discard the chosen energy cards and remove them from Pokémon
                for energy_card in chosen_cards:
                    # Find which Pokémon has this energy
                    source_pokemon = None
                    for pokemon in current_all_pokemon(state):
                        if energy_card in pokemon.attachment:
                            source_pokemon = pokemon
                            break

                    # Construct proper source position based on Pokémon's position
                    if source_pokemon:
                        if source_pokemon.cardPosition == CardPosition.ACTIVE:
                            source_pos = (player.id, CardPosition.ACTIVE_ATTACHMENT)
                        else:  # CardPosition.BENCH
                            source_pos = (
                                player.id,
                                CardPosition.BENCH_ATTACHMENT,
                                source_pokemon.index,
                            )

                        # Move to discard pile
                        move_cards(
                            energy_card,
                            source_pos,
                            (player.id, CardPosition.DISCARD),
                            state,
                        )

                        # Remove energy type from Pokémon's energy list after moving the card
                        for energy_type in energy_card.provides:
                            if energy_type in source_pokemon.energy:
                                source_pokemon.energy.remove(energy_type)

                # Calculate damage: 60 per discarded energy
                discarded_count = len(chosen_cards)
                action.attack.damage = 60 * discarded_count
            else:
                # No energy discarded, use base damage
                action.attack.damage = 60
        else:
            # No Lightning Energy available, use base damage
            action.attack.damage = 60

        # Execute the attack with calculated damage
        yield from reduce_attack_action(action, state)
