from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class TWM152HyperAroma(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TWM"
        self.number = "152"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Hyper Aroma"
        self.cardType = CardType.NONE
        self.text = "Search your deck for up to 3 Stage 1 Pokémon, reveal them, and put them into your hand. Then, shuffle your deck."

    def get_actions(self, state):
        """Check if card can be used"""
        player = current_player(state)
        actions = []

        # Can use if deck has enough cards
        if len(player.left) >= 1:
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

            # Find Stage 1 Pokémon in deck
            stage1_pokemon = [
                card
                for card in player.left
                if card.superType == SuperType.POKEMON and card.stage == Stage.STAGE_1
            ]

            if stage1_pokemon:
                # Let player choose up to 3 Stage 1 Pokémon
                tips = "You used Hyper Aroma. You may choose up to 3 Stage 1 Pokémon from your deck to reveal and add to your hand."
                actions = choose_card_actions(
                    player.id,
                    player.id,
                    0,
                    min(3, len(stage1_pokemon)),
                    stage1_pokemon,
                    tips=tips,
                    source=self,
                )
                chosen_pokemon = yield from reduce_choose_card_actions(actions, state)

                # Move chosen Pokémon to hand
                if chosen_pokemon and all(pokemon in player.left for pokemon in chosen_pokemon):
                    move_cards(
                        chosen_pokemon,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.HAND),
                        state,
                    )

            # Shuffle deck
            shuffle_cards(player.left)
