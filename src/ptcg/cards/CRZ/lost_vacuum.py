from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard, PokemonCard, StadiumCard, ToolCard
from ptcg.core.enums import *
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class CRZ135LostVacuum(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "CRZ"
        self.number = "135"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Lost Vacuum"
        self.cardType = CardType.NONE
        self.text = (
            "You can use this card only if you put another card from your hand in the Lost Zone. "
            "Choose a Pokémon Tool attached to any Pokémon, or any Stadium in play, and put it in the Lost Zone."
        )

    def get_actions(self, state):
        actions = []

        cards = self.get_tool_and_stadium(state)
        if len(current_player(state).hand) >= 2 and len(cards) >= 1:
            actions.append(UseItemAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            opponent = opponent_player(state)

            # discard self
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            # hand
            tips = "You used Lost Vacuum. You need to put 1 card from your hand in the Lost Zone."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, player.hand, tips=tips, source=self
            )
            target = yield from reduce_choose_card_actions(actions, state)
            move_cards(
                target, (player.id, CardPosition.HAND), (player.id, CardPosition.LOSTZONE), state
            )

            # tool or stadium
            cards = self.get_tool_and_stadium(state)
            tips = "You used Lost Vacuum. You can choose a Tool or a Stadium in play, and put it in the Lost Zone."
            actions = choose_card_actions(player.id, player.id, 1, 1, cards, tips=tips, source=self)
            target = yield from reduce_choose_card_actions(actions, state)
            target = target[0]

            if isinstance(target, StadiumCard):
                if target in state.stadium and target.playedFrom == player.id:
                    move_cards(
                        target,
                        (None, CardPosition.STADIUM),
                        (player.id, CardPosition.LOSTZONE),
                        state,
                    )
                elif target in state.stadium and target.playedFrom == opponent.id:
                    move_cards(
                        target,
                        (None, CardPosition.STADIUM),
                        (opponent.id, CardPosition.LOSTZONE),
                        state,
                    )
            elif isinstance(target, PokemonCard):
                if target in current_all_pokemon(state):
                    tool = [card for card in target.attachment if isinstance(card, ToolCard)]
                    if target.cardPosition == CardPosition.ACTIVE:
                        move_cards(
                            tool[0],
                            (player.id, CardPosition.ACTIVE_ATTACHMENT, target.index),
                            (player.id, CardPosition.LOSTZONE),
                            state,
                        )
                    else:
                        move_cards(
                            tool[0],
                            (player.id, CardPosition.BENCH_ATTACHMENT, target.index),
                            (player.id, CardPosition.LOSTZONE),
                            state,
                        )
                elif target in opponent_all_pokemon(state):
                    tool = [card for card in target.attachment if isinstance(card, ToolCard)]
                    if target.cardPosition == CardPosition.ACTIVE:
                        move_cards(
                            tool[0],
                            (opponent.id, CardPosition.ACTIVE_ATTACHMENT, target.index),
                            (opponent.id, CardPosition.LOSTZONE),
                            state,
                        )
                    else:
                        move_cards(
                            tool[0],
                            (opponent.id, CardPosition.BENCH_ATTACHMENT, target.index),
                            (opponent.id, CardPosition.LOSTZONE),
                            state,
                        )

    def get_tool_and_stadium(self, state):
        current_player(state)
        opponent_player(state)

        cards = []
        for pokemon in current_all_pokemon(state) + opponent_all_pokemon(state):
            for attachment in pokemon.attachment:
                if isinstance(attachment, ToolCard):
                    cards.append(pokemon)  # PokemonCard
        cards.extend(state.stadium)

        return cards
