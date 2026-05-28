from ptcg.core.action import EvolvePokemonAction, UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard, PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class PAF089RareCandy(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAF"
        self.number = "089"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Rare Candy"
        self.cardType = CardType.NONE
        self.text = "Choose 1 of your Basic Pokémon in play. If you have a Stage 2 card in your hand that evolves from that Pokémon, put that card on the Basic Pokémon. (This counts as evolving that Pokémon.) You can't use this card during your first turn or on a Basic Pokémon that was put into play this turn."

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        found = False
        for card in player.hand:
            if not (isinstance(card, PokemonCard) and card.stage == Stage.STAGE_2):
                continue
            for pokemon in current_all_pokemon(state):
                if pokemon.name == card.evolveFrom[-1] and not pokemon.firstTurnPlayed:
                    found = True
                    break

        if found:
            actions.append(UseItemAction(player.id, self))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)

            # discard self
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            # combinations = []
            evolved_cardlist = []
            for card in player.hand:
                if not (isinstance(card, PokemonCard) and card.stage == Stage.STAGE_2):
                    continue
                for pokemon in current_all_pokemon(state):
                    if pokemon.name == card.evolveFrom[-1]:
                        evolved_cardlist.append(card)
                        break

            tips = "You used Rare Candy. You should choose a stage 2 Pokemon in your hand for evolution."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, evolved_cardlist, tips=tips, source=self
            )
            evolved_card = yield from reduce_choose_card_actions(actions, state)
            evolved_card = evolved_card[0]

            evolving_cardlist = []
            for pokemon in current_all_pokemon(state):
                if pokemon.name == evolved_card.evolveFrom[-1]:
                    evolving_cardlist.append(pokemon)

            tips = "You used Rare Candy. You should choose a basic Pokemon in play to evolve."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, evolving_cardlist, tips=tips, source=self
            )
            evolving_card = yield from reduce_choose_card_actions(actions, state)
            evolving_card = evolving_card[0]

            yield from evolved_card.reduce_action(
                EvolvePokemonAction(player.id, evolved_card, evolving_card), state
            )
