from ptcg.core.ability import ActiveAbility
from ptcg.core.action import UseAbilityAction, UseToolAction, choose_card_actions
from ptcg.core.card import ToolCard
from ptcg.core.enums import *
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import *


class SIT156ForestSealStone(ToolCard):
    def __init__(self):
        super().__init__()
        self.set_name = "SIT"
        self.number = "156"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Forest Seal Stone"
        self.cardType = CardType.NONE
        self.text = "The Pokémon V this card is attached to can use the VSTAR Power on this card."

        self.ability = [
            ActiveAbility(
                {
                    "name": "Star Alchemy",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "text": "During your turn, you may search your deck for a card and put it into your hand. "
                    "Then, shuffle your deck. (You can't use more than 1 VSTAR Power in a game.)",
                }
            )
        ]

        self.hasAttached = False
        self.attachedTo = None
        self.cardTag = CardTag.VSTAR

    def get_actions(self, state):
        actions = []
        player = current_player(state)

        if not self.hasAttached:
            actions.extend(
                UseToolAction(state.turn, self, card)
                for card in current_all_pokemon(state)
                if can_attach_tool(card)
            )

        if (
            self.hasAttached
            and player.onceUsedGame.get(CardTag.VSTAR) is False
            and self.attachedTo[0].pokemonType == PokemonType.V
        ):
            for ability in self.ability:
                actions.append(UseAbilityAction(player.id, self, ability))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseToolAction):
            player = current_player(state)
            target = action.target
            target_position = (
                CardPosition.ACTIVE_ATTACHMENT
                if target.cardPosition == CardPosition.ACTIVE
                else CardPosition.BENCH_ATTACHMENT
            )
            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, target_position, target.index),
                state,
            )
            self.hasAttached = True
            self.attachedTo = [target]

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            cards = player.left
            tips = "You used the ability Star Alchemy. You can choose up to 1 card from your deck and put it into your hand."
            actions = choose_card_actions(player.id, player.id, 0, 1, cards, tips=tips, source=self)
            chosen_card = yield from reduce_choose_card_actions(actions, state)

            if all(card in player.left for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )
            shuffle_cards(player.left)

            player.onceUsedGame.update({CardTag.VSTAR: True})
