from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, SuperType, TrainerType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards


class TWM163SecretBox(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "TWM"
        self.number = "163"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Secret Box"
        self.cardType = CardType.NONE
        self.text = (
            "You can use this card only if you discard 3 other cards from your hand. "
            "Search your deck for an Item card, a Pokémon Tool card, a Supporter card, and a Stadium card, "
            "reveal them, and put them into your hand. Then, shuffle your deck."
        )

    def get_actions(self, state):
        player = current_player(state)
        other_hand = [c for c in player.hand if c is not self]
        if len(other_hand) >= 3:
            return [UseItemAction(state.turn, self)]
        return []

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)

            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            other_hand = [c for c in player.hand]
            tips = "You used Secret Box. Choose 3 cards from your hand to discard."
            discard_actions = choose_card_actions(
                player.id, player.id, 3, 3, other_hand, tips=tips, source=self
            )
            to_discard = yield from reduce_choose_card_actions(discard_actions, state)

            for card in to_discard:
                if card in player.hand:
                    move_cards(
                        card,
                        (player.id, CardPosition.HAND),
                        (player.id, CardPosition.DISCARD),
                        state,
                    )

            items = [
                c
                for c in player.left
                if c.superType == SuperType.TRAINER and c.trainerType == TrainerType.ITEM
            ]
            tools = [
                c
                for c in player.left
                if c.superType == SuperType.TRAINER and c.trainerType == TrainerType.TOOL
            ]
            supporters = [
                c
                for c in player.left
                if c.superType == SuperType.TRAINER and c.trainerType == TrainerType.SUPPORTER
            ]
            stadiums = [
                c
                for c in player.left
                if c.superType == SuperType.TRAINER and c.trainerType == TrainerType.STADIUM
            ]

            for card_pool, label in [
                (items, "Item"),
                (tools, "Pokémon Tool"),
                (supporters, "Supporter"),
                (stadiums, "Stadium"),
            ]:
                if card_pool:
                    tips = f"You used Secret Box. Choose 1 {label} card from your deck to put into your hand."
                    pick_actions = choose_card_actions(
                        player.id, player.id, 0, 1, card_pool, tips=tips, source=self
                    )
                    chosen = yield from reduce_choose_card_actions(pick_actions, state)
                    if chosen:
                        move_cards(
                            chosen[0],
                            (player.id, CardPosition.LEFT),
                            (player.id, CardPosition.HAND),
                            state,
                        )

            shuffle_cards(player.left)
