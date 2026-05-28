from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.utils.utils import *


class ASR154SwitchCart(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "154"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Switch Cart"
        self.cardType = CardType.NONE
        self.text = "Switch your Active Basic Pokémon with 1 of your Benched Pokémon. If you do, heal 30 damage from Pokémon you moved to your Bench."

    def get_actions(self, state):
        """Check if card can be used"""
        player = current_player(state)
        actions = []

        # Can use if active Pokémon is Basic and has benched Pokémon
        if player.active and player.active[0].stage == Stage.BASIC and len(player.bench) >= 1:
            actions.append(UseItemAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        """Execute effect"""
        if isinstance(action, UseItemAction):
            player = current_player(state)

            # Discard this card
            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            # Switch active Basic Pokémon with benched Pokémon
            if player.active and player.active[0].stage == Stage.BASIC and len(player.bench) >= 1:
                active_pokemon = player.active[0]
                benched_pokemon = player.bench[0]

                # Store max_hp if not already tracked
                if not hasattr(benched_pokemon, "max_hp"):
                    benched_pokemon.max_hp = benched_pokemon.hp

                # Switch positions using switch_pokemon utility
                switch_pokemon(active_pokemon, benched_pokemon, player)

                # Heal 30 damage from the Pokémon moved to bench
                benched_pokemon.hp = min(
                    benched_pokemon.hp + 30,
                    benched_pokemon.max_hp,
                )
