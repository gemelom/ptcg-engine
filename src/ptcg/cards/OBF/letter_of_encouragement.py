from ptcg.core.action import DiscardStadiumAction, PutStadiumAction
from ptcg.core.card import StadiumCard
from ptcg.core.enums import *
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class OBF189LetterofEncouragement(StadiumCard):
    def __init__(self):
        super().__init__()
        self.set_name = "OBF"
        self.number = "189"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Letter of Encouragement"
        self.cardType = CardType.NONE
        self.text = "You can use this card only if any of your Pokémon were Knocked Out during your opponent’s last turn. Search your deck for up to 3 Basic Energy cards, reveal them, and put them into your hand. Then, shuffle your deck."

    def get_actions(self, state):
        """Return list of currently available actions"""
        actions = []
        player = current_player(state)

        # Can use if opponent knocked out a Pokémon last turn
        if player.hasPokemonDead and not state.stadium:
            # Can use if bench has space
            if player.benchSize - len(player.bench) >= 1:
                actions.append(PutStadiumAction(player.id, self))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, PutStadiumAction):
            player = current_player(state)

            # 1. Discard old stadium if exists
            if state.stadium:
                old_stadium = state.stadium[0]
                result = old_stadium.reduce_action(
                    DiscardStadiumAction(old_stadium.playedFrom, old_stadium), state
                )
                if result is not None:
                    yield from result

            # 2. Check knockouts and get energy cards
            energy_cards = [
                card
                for card in player.left
                if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
            ]

            max_energy = min(len(energy_cards), 3)

            # Let player choose energy cards
            if energy_cards:
                tips = "You used Letter of Encouragement. You may choose up to 3 Basic Energy cards from your deck to add to your hand."
                actions = choose_card_actions(
                    player.id,
                    player.id,
                    0,
                    max_energy,
                    energy_cards,
                    tips=tips,
                    source=self,
                )
                chosen_energy = yield from reduce_choose_card_actions(actions, state)

                # Move chosen energy to hand
                if chosen_energy and all(card in player.left for card in chosen_energy):
                    move_cards(
                        chosen_energy,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.HAND),
                        state,
                    )

            # 3. Search deck for basic energy cards (backup for draw)
            if player.hasPokemonDead and len(player.left) >= 3:
                basic_energy = [
                    card
                    for card in player.left
                    if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
                ]

                if basic_energy:
                    # Reveal up to 3 and put in hand
                    cards_to_reveal = basic_energy[:3]
                    for card in cards_to_reveal:
                        move_cards(
                            card,
                            (player.id, CardPosition.LEFT),
                            (player.id, CardPosition.HAND),
                            state,
                        )

                    # Shuffle deck
                    shuffle_cards(player.left)

            # 4. Discard this card and play it
            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.STADIUM),
                state,
            )

            # 5. Set this as the stadium
            self.playedFrom = player.id
            state.stadium = [self]
