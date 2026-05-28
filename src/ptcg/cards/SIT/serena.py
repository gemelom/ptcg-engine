from typing import cast

from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import Card, SupporterCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class SIT164Serena(SupporterCard):
    def __init__(self):
        super().__init__()
        self.set_name = "SIT"
        self.number = "164"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Serena"
        self.cardType = CardType.NONE
        self.text = "Choose 1: • Discard up to 3 cards from your hand. (You must discard at least 1 card.) If you do, draw cards until you have 5 cards in your hand. • Switch 1 of your opponent's Benched Pokémon V with their Active Pokémon."

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        effect1_possible = len(player.hand) >= 1
        effect2_possible = len(opponent_player(state).bench) >= 1

        if not player.supporterPlayedTurn and (effect1_possible or effect2_possible):
            actions.append(UseSupporterAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            opponent = opponent_player(state)

            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            choice_cards = cast(
                list[Card],
                [
                    self._Effect1Card("Effect 1: Discard & Draw"),
                    self._Effect2Card("Effect 2: Switch Pokemon V"),
                ],
            )

            tips = "Choose an effect: (1) Discard 1-3 cards and draw to 5, or (2) Switch opponent's benched Pokemon V with their active Pokemon."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, choice_cards, tips=tips, source=self
            )
            chosen = yield from reduce_choose_card_actions(actions, state)
            chosen = chosen[0]

            if isinstance(chosen, self._Effect1Card):
                yield from self._effect_discard_draw(player, state)
            elif isinstance(chosen, self._Effect2Card):
                yield from self._effect_switch_v(opponent, state)

            player.supporterPlayedTurn = True

    def _effect_discard_draw(self, player, state):
        max_discard = min(3, len(player.hand))
        if max_discard < 1:
            return
        tips = f"Choose 1 to {max_discard} cards from your hand to discard."
        actions = choose_card_actions(
            player.id, player.id, 1, max_discard, player.hand, tips=tips, source=self
        )
        to_discard = yield from reduce_choose_card_actions(actions, state)

        for card in to_discard:
            move_cards(
                card, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

        cards_to_draw = min(5 - len(player.hand), len(player.left))
        for _ in range(cards_to_draw):
            move_cards(
                player.left[0],
                (player.id, CardPosition.LEFT),
                (player.id, CardPosition.HAND),
                state,
            )

    def _effect_switch_v(self, opponent, state):
        benched_vs = [p for p in opponent.bench if p.pokemonType == PokemonType.V]

        if not benched_vs:
            return

        tips = "Choose 1 of your opponent's Benched Pokemon V to switch with their Active Pokemon."
        actions = choose_card_actions(state.turn, opponent.id, 1, 1, benched_vs, tips=tips)
        chosen_v = yield from reduce_choose_card_actions(actions, state)
        chosen_v = chosen_v[0]

        if chosen_v in opponent.bench and opponent.active:
            switch_pokemon(chosen_v, opponent.active[0], opponent)

    class _Effect1Card(Card):
        def __init__(self, name):
            super().__init__()
            self.name = name
            self.set_name = "SIT"
            self.number = "164"
            self.cardType = CardType.NONE

        def get_actions(self, state):
            return []

    class _Effect2Card(Card):
        def __init__(self, name):
            super().__init__()
            self.name = name
            self.set_name = "SIT"
            self.number = "164"
            self.cardType = CardType.NONE

        def get_actions(self, state):
            return []
