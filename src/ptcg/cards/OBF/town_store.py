from ptcg.core.action import (
    DiscardStadiumAction,
    PutStadiumAction,
    UseStadiumAction,
    choose_card_actions,
)
from ptcg.core.card import StadiumCard, ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import (
    current_player,
    discard_card,
    move_cards,
    opponent_player,
    shuffle_cards,
)


class OBF196TownStore(StadiumCard):
    def __init__(self):
        super().__init__()
        self.set_name = "OBF"
        self.number = "196"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Town Store"
        self.cardType = CardType.NONE
        self.text = (
            "Once during each player's turn, that player may search their deck for a "
            "Pokémon Tool card, reveal it, and put it into their hand. Then, that player shuffles their deck."
        )
        self.playedFrom = None

    def get_actions(self, state):
        actions = []
        player = current_player(state)

        # Play from hand
        if not player.stadiumPlayedTurn and self in player.hand:
            actions.append(PutStadiumAction(player.id, self))

        # Once-per-turn search effect (engine checks stadiumUsedTurn before calling this)
        if state.stadium and self in state.stadium:
            tools = [card for card in player.left if isinstance(card, ToolCard)]
            if tools:
                actions.append(UseStadiumAction(player.id, self))

        return actions

    def reduce_action(self, action, state):
        player = current_player(state)

        if isinstance(action, PutStadiumAction):
            if state.stadium:
                old_stadium = state.stadium[0]
                try:
                    result = old_stadium.reduce_action(
                        DiscardStadiumAction(old_stadium.playedFrom, old_stadium), state
                    )
                    if result is not None:
                        yield from result
                except StopIteration:
                    pass

            self.playedFrom = player.id
            player.stadiumPlayedTurn = True
            move_cards(
                action.source, (player.id, CardPosition.HAND), (None, CardPosition.STADIUM), state
            )

        elif isinstance(action, UseStadiumAction):
            tools = [card for card in player.left if isinstance(card, ToolCard)]
            tips = "You used Town Store. Choose 1 Pokémon Tool card from your deck to put into your hand."
            actions = choose_card_actions(player.id, player.id, 1, 1, tools, tips=tips, source=self)
            chosen = yield from reduce_choose_card_actions(actions, state)
            if chosen:
                move_cards(
                    chosen,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )
            shuffle_cards(player.left)
            player.stadiumUsedTurn = True

        elif isinstance(action, DiscardStadiumAction):
            state.stadium.remove(self)
            owner = (
                current_player(state) if self.playedFrom == player.id else opponent_player(state)
            )
            discard_card(owner, self)
