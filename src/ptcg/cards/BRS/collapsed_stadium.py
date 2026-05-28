from ptcg.core.action import (
    DiscardStadiumAction,
    PutStadiumAction,
    UseStadiumAction,
    choose_card_actions,
)
from ptcg.core.card import StadiumCard
from ptcg.core.enums import *
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class BRS137CollapsedStadium(StadiumCard):
    def __init__(self):
        super().__init__()
        self.set_name = "BRS"
        self.number = "137"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Collapsed Stadium"
        self.cardType = CardType.NONE
        self.text = (
            "Each player can't have more than 4 Benched Pokémon. "
            "If a player has 5 or more Benched Pokémon, they discard"
            "Benched Pokémon until they have 4 Pokémon on the Bench. "
            "The player who played this card discards first. If more"
            "than one effect changes the number of Benched Pokémon"
            "allowed, use the smaller number."
        )

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.stadiumPlayedTurn and self in player.hand:
            actions.append(PutStadiumAction(player.id, self))
        # if not player.stadiumUsedTurn:
        #     actions.append(UseStadiumAction(player.id, self))

        return actions

    def reduce_action(self, action, state):
        # instant
        if isinstance(action, PutStadiumAction):
            player = current_player(state)
            opponent = opponent_player(state)

            if len(state.stadium) > 0:
                old_stadium = state.stadium[0]
                try:
                    result = old_stadium.reduce_action(
                        DiscardStadiumAction(old_stadium.playedFrom, old_stadium), state
                    )
                    if result is not None:
                        yield from result
                except StopIteration:
                    pass

            player.benchSize = 4
            opponent.benchSize = 4

            self.playedFrom = player.id

            player.stadiumPlayedTurn = True
            move_cards(
                action.source, (player.id, CardPosition.HAND), (None, CardPosition.STADIUM), state
            )

            # discard extra pokemon
            if len(player.bench) > 4:
                discard_cnt = len(player.bench) - 4
                tips = f"Collapsed Stadium is now activated. You have to choose {discard_cnt} pokemon(s) in your bench to discard."
                actions = choose_card_actions(
                    player.id,
                    player.id,
                    discard_cnt,
                    discard_cnt,
                    player.bench,
                    tips=tips,
                    source=self,
                )
                chosen_pokemon = yield from reduce_choose_card_actions(actions, state)
                if chosen_pokemon:
                    for pokemon in chosen_pokemon:
                        discard_pokemon(player, pokemon)
                    for idx, card in enumerate(player.bench):
                        card.index = idx + 1

            if len(opponent.bench) > 4:
                old_turn = state.turn
                state.turn = opponent.id
                discard_cnt = len(opponent.bench) - 4
                tips = f"Collapsed Stadium is now activated. You have to choose {discard_cnt} pokemon(s) in your bench to discard."
                actions = choose_card_actions(
                    opponent.id,
                    opponent.id,
                    discard_cnt,
                    discard_cnt,
                    opponent.bench,
                    tips=tips,
                    source=self,
                )
                chosen_pokemon = yield from reduce_choose_card_actions(actions, state)
                if chosen_pokemon:
                    for pokemon in chosen_pokemon:
                        discard_pokemon(opponent, pokemon)
                    for idx, card in enumerate(opponent.bench):
                        card.index = idx + 1
                state.turn = old_turn

        # active
        elif isinstance(action, UseStadiumAction):
            pass

        # discard effect
        elif isinstance(action, DiscardStadiumAction):
            player = current_player(state)
            opponent = opponent_player(state)
            player.benchSize = 5
            opponent.benchSize = 5

            old_stadium = action.source
            state.stadium.remove(old_stadium)
            if old_stadium.playedFrom == player.id:
                discard_card(player, old_stadium)
            elif old_stadium.playedFrom == opponent.id:
                discard_card(opponent, old_stadium)
