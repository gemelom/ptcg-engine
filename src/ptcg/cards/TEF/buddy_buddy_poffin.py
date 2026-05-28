from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class TEF144BuddyBuddyPoffin(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "144"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Buddy-Buddy Poffin"
        self.cardType = CardType.NONE
        self.text = "Search your deck for up to 2 Basic Pokémon with 70 HP or less and put them onto your Bench. Then, shuffle your deck."

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
            if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC and card.hp <= 70
        ]
        bench_left = player.benchSize - len(player.bench)

        if isinstance(action, UseItemAction):
            tips = f"You used Buddy Buddy Poffin. You can choose up to {min(len(cards), bench_left, 2)} Pokemon(s) from your deck, and put them onto your bench."
            actions = choose_card_actions(
                player.id,
                player.id,
                0,
                min(len(cards), bench_left, 2),
                cards,
                tips=tips,
                source=self,
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.left for card in chosen_card):
                for card in chosen_card:
                    player.left.remove(card)
                    player.bench.append(card)
                    card.position = PokemonPosition.BENCH
                    card.cardPosition = CardPosition.BENCH
                for idx, card in enumerate(player.left):
                    card.index = idx + 1
                for idx, card in enumerate(player.bench):
                    card.index = idx + 1
            else:
                print(chosen_card)
                print(player.left)
                raise ValueError(f"Invalid action: {action}")

            shuffle_cards(player.left)
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )
