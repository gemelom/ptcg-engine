from ptcg.core.action import (
    DiscardStadiumAction,
    PutStadiumAction,
    UseStadiumAction,
    choose_card_actions,
)
from ptcg.core.card import StadiumCard
from ptcg.core.enums import CardPosition, CardType, PokemonRule, Stage, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import (
    current_player,
    discard_card,
    move_cards,
    opponent_player,
    shuffle_cards,
)


class PAL171Artazon(StadiumCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "171"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Artazon"
        self.cardType = CardType.NONE
        self.text = (
            "Once during each player's turn, that player may search their deck for a "
            "Basic Pokémon that doesn't have a Rule Box and put it onto their Bench. "
            "Then, that player shuffles their deck. (Pokémon ex, Pokémon V, etc. have "
            "Rule Boxes.)"
        )
        self.playedFrom = None

    def get_actions(self, state):
        actions = []
        player = current_player(state)

        if not player.stadiumPlayedTurn and self in player.hand:
            actions.append(PutStadiumAction(player.id, self))

        if state.stadium and self in state.stadium:
            basic_pokemon = [
                card
                for card in player.left
                if card.superType == SuperType.POKEMON
                and card.stage == Stage.BASIC
                and card.pokemonRule == PokemonRule.NONE
            ]
            if basic_pokemon and len(player.bench) < player.benchSize:
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
            basic_pokemon = [
                card
                for card in player.left
                if card.superType == SuperType.POKEMON
                and card.stage == Stage.BASIC
                and card.pokemonRule == PokemonRule.NONE
            ]
            tips = (
                "You used Artazon. You may choose 1 Basic Pokémon that doesn't have a "
                "Rule Box from your deck to put onto your Bench."
            )
            actions = choose_card_actions(
                player.id, player.id, 1, 1, basic_pokemon, tips=tips, source=self
            )
            chosen = yield from reduce_choose_card_actions(actions, state)
            if chosen:
                move_cards(
                    chosen,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.BENCH),
                    state,
                )
            shuffle_cards(player.left)
            player.stadiumUsedTurn = True

        elif isinstance(action, DiscardStadiumAction):
            state.stadium.remove(self)
            owner = player if self.playedFrom == player.id else opponent_player(state)
            discard_card(owner, self)
