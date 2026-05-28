from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class PAR257ProfessorTurosScenario(SupporterCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "257"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Professor Turo's Scenario"
        self.cardType = CardType.NONE
        self.text = "Put 1 of your Pokémon in play into your hand. (Discard all cards attached to that Pokémon.)"

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        if not player.supporterPlayedTurn and len(current_all_pokemon(state)) > 1:
            actions.extend([UseSupporterAction(state.turn, self)])

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)

            # discard self
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            tips = "You used Professor Turo's Scenario. You should choose 1 of your Pokemon and put it into your hand. Then, discard all cards attached to that Pokemon."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, current_all_pokemon(state), tips=tips, source=self
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            chosen_card = chosen_card[0]

            if chosen_card.position == PokemonPosition.ACTIVE:
                player.active.remove(chosen_card)
                # choose a new active
                tips = "You used Professor Turo's Scenario and choose the active Pokemon. You should choose 1 of your benched Pokemon and switch it onto active spot."
                actions = choose_card_actions(
                    player.id, player.id, 1, 1, current_bench(state), tips=tips, source=self
                )
                chosen_card = yield from reduce_choose_card_actions(actions, state)
                chosen_card = chosen_card[0]
                move_pokemon(player, chosen_card)

            elif chosen_card.position == PokemonPosition.BENCH:
                player.bench.remove(chosen_card)
                for idx, card in enumerate(player.bench):
                    card.index = idx + 1

            # pokemon to hand
            item = type(chosen_card)()
            item.cardPosition = CardPosition.HAND
            item.index = len(player.hand) + 1
            player.hand.append(item)

            # evolveFrom pokemon to hand
            if chosen_card.stage != Stage.BASIC:
                for pokemon in chosen_card.evolved:
                    discard_card(player, pokemon)

            for card in chosen_card.attachment:
                discard_card(player, card)
            player.supporterPlayedTurn = True
