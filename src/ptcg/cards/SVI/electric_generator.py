from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import (
    CardPosition,
    CardType,
    EnergyType,
    SuperType,
)
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards


class SVI170ElectricGenerator(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "SVI"
        self.number = "170"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Electric Generator"
        self.cardType = CardType.NONE
        self.text = "Look at the top 5 cards of your deck and attach up to 2 Basic [L] Energy cards you find there to your Benched [L] Pokémon in any way you like. Shuffle the other cards back into your deck."

    def get_actions(self, state):
        player = current_player(state)
        actions = []

        # Check if there are benched Lightning Pokemon to attach energy to
        lightning_bench_pokemon = [
            pokemon for pokemon in player.bench if pokemon.cardType == CardType.LIGHTNING
        ]

        # Only allow using this card if there are Lightning Pokemon on bench and cards in deck
        if lightning_bench_pokemon and len(player.left) > 0:
            actions.append(UseItemAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)

            # Discard self first
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            # Look at the top 5 cards of the deck
            look_count = min(5, len(player.left))
            top_cards = player.left[:look_count]

            # Find Basic Lightning Energy cards among the top cards
            lightning_energy_cards = [
                card
                for card in top_cards
                if card.superType == SuperType.ENERGY
                and card.energyType == EnergyType.BASIC
                and CardType.LIGHTNING in card.provides
            ]

            if lightning_energy_cards:
                # First, choose up to 2 Basic Lightning Energy cards
                tips = "You used Electric Generator. You may choose up to 2 Basic Lightning Energy cards from the top 5 cards of your deck."
                actions = choose_card_actions(
                    player.id,
                    player.id,
                    0,
                    min(len(lightning_energy_cards), 2),
                    lightning_energy_cards,
                    tips=tips,
                    source=self,
                )

                chosen_energies = yield from reduce_choose_card_actions(actions, state)

                if chosen_energies:
                    # Get benched Lightning Pokemon for targeting
                    lightning_bench_pokemon = [
                        pokemon
                        for pokemon in player.bench
                        if pokemon.cardType == CardType.LIGHTNING
                    ]

                    # Attach each chosen energy to a benched Lightning Pokemon
                    for energy_card in chosen_energies:
                        if lightning_bench_pokemon:
                            tips = f"Choose 1 of your Benched Lightning Pokémon to attach {energy_card.name} to."
                            actions = choose_card_actions(
                                player.id,
                                player.id,
                                1,
                                1,
                                lightning_bench_pokemon,
                                tips=tips,
                                source=self,
                            )

                            target_pokemon = yield from reduce_choose_card_actions(actions, state)
                            target_pokemon = target_pokemon[0]

                            # Attach energy to the chosen Pokemon
                            provides = energy_card.provides
                            target_pokemon.energy.extend(provides)

                            # Move energy card from deck to attachment
                            move_cards(
                                energy_card,
                                (player.id, CardPosition.LEFT),
                                (player.id, CardPosition.BENCH_ATTACHMENT, target_pokemon.index),
                                state,
                            )

            # Shuffle the remaining cards back into the deck
            shuffle_cards(player.left)

        else:
            raise ValueError(f"Invalid action: {action}")
