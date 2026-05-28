from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType, Stage, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards


class SVI175Jacq(SupporterCard):
    def __init__(self):
        super().__init__()
        self.set_name = "SVI"
        self.number = "175"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Jacq"
        self.cardType = CardType.NONE
        self.text = "Search your deck for up to 2 Evolution Pokémon, reveal them, and put them into your hand. Then, shuffle your deck."

    def get_actions(self, state):
        player = current_player(state)
        actions = []

        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)

            # Discard self to discard pile
            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            # Search deck for Evolution Pokemon (Pokemon with stage != BASIC)
            evolution_pokemon = [
                card
                for card in player.left
                if card.superType == SuperType.POKEMON and card.stage != Stage.BASIC
            ]

            if evolution_pokemon:
                # Let player choose up to 2 Evolution Pokemon
                tips = "You used Jacq. You may choose up to 2 Evolution Pokémon from your deck."
                actions = choose_card_actions(
                    player.id,
                    player.id,
                    0,
                    min(len(evolution_pokemon), 2),
                    evolution_pokemon,
                    tips=tips,
                    source=self,
                )

                chosen_cards = yield from reduce_choose_card_actions(actions, state)

                # Put chosen cards in hand
                for card in chosen_cards:
                    move_cards(
                        card,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.HAND),
                        state,
                    )

            # Shuffle deck
            shuffle_cards(player.left)

            # Set supporterPlayedTurn = True
            player.supporterPlayedTurn = True
