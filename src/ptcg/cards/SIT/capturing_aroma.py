from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class SIT153CapturingAroma(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "SIT"
        self.number = "153"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Capturing Aroma"
        self.cardType = CardType.NONE
        self.text = (
            "Flip a coin. If heads, search your deck for an Evolution Pokémon, reveal it, "
            "and put it into your hand. If tails, search your deck for a Basic Pokémon, "
            "reveal it, and put it into your hand. Then, shuffle your deck."
        )

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand:
            actions.append(UseItemAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)

            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            coin_result = flip_coin(state)

            if coin_result == Coin.HEAD:
                cards = [
                    card
                    for card in player.left
                    if card.superType == SuperType.POKEMON
                    and card.stage in [Stage.STAGE_1, Stage.STAGE_2]
                ]
                tips = "Heads! You used Capturing Aroma. You can choose up to 1 Evolution Pokémon (Stage 1 or Stage 2) from your deck and put it into your hand."
            else:
                cards = [
                    card
                    for card in player.left
                    if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
                ]
                tips = "Tails! You used Capturing Aroma. You can choose up to 1 Basic Pokémon from your deck and put it into your hand."

            actions = choose_card_actions(player.id, player.id, 0, 1, cards, tips=tips, source=self)
            chosen_card = yield from reduce_choose_card_actions(actions, state)

            if len(chosen_card) == 1 and all(card in player.left for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )
            elif len(chosen_card) == 0:
                pass
            else:
                raise ValueError(f"Invalid action: {action}")

            shuffle_cards(player.left)
