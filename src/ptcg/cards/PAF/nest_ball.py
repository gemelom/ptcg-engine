from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class PAF084NestBall(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAF"
        self.number = "084"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Nest Ball"
        self.cardType = CardType.NONE
        self.text = "Search your deck for a Basic Pokémon and put it onto your Bench. Then, shuffle your deck."

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        if player.benchSize - len(player.bench) >= 1:
            actions.extend([UseItemAction(state.turn, self)])

        return actions

    def reduce_action(self, action, state):
        player = current_player(state)
        cards = [
            card
            for card in player.left
            if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
        ]

        if isinstance(action, UseItemAction):
            # discard self
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            tips = "You used Nest Ball. You can choose up to 1 basic Pokemon from your deck and put it onto your Bench."
            actions = choose_card_actions(player.id, player.id, 0, 1, cards, tips=tips, source=self)
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if len(chosen_card) == 0:
                pass
            elif len(chosen_card) == 1 and all(card in player.left for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.BENCH),
                    state,
                )
                chosen_card[0].position = PokemonPosition.BENCH
            else:
                raise ValueError(f"Invalid action: {action}")

            shuffle_cards(player.left)
