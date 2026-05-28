from ptcg.core.ability import *
from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardType,
    PokemonRule,
    PokemonType,
    Stage,
    SuperType,
    TrainerType,
)
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class BRS040LumineonV(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "BRS"
        self.number = "040"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Lumineon V"
        self.hp = 170
        self.pokemonType = PokemonType.V
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = []
        self.prize = 2

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Aqua Return",
                    "damage": 120,
                    "cost": [CardType.WATER, CardType.COLORLESS, CardType.COLORLESS],
                    "text": "Shuffle this Pokémon and all attached cards into your deck.",
                }
            )
        ]

        self.ability = [
            InstantAbility(
                {
                    "name": "Luminous Sign",
                    "abilityType": AbilityType.INSTANT_ABILITY,
                    "onceUsedPerTurn": False,
                    "text": "When you play this Pokémon from your hand onto your Bench during your turn, "
                    "you may search your deck for a Supporter card, reveal it, and put it into your hand. Then, shuffle your deck.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy) and len(current_player(state).bench) >= 1:
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        return actions

    def use_ability(self, action, state):
        if isinstance(action, PlayPokemonAction):
            player = current_player(state)
            cards = [
                card
                for card in player.left
                if card.superType == SuperType.TRAINER and card.trainerType == TrainerType.SUPPORTER
            ]

            tips = "You used the ability Luminous Sign. You can choose up to 1 Supporter card from your deck and put it into your hand."
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

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

            # Luminous Sign
            player = current_player(state)
            if action.position == PokemonPosition.BENCH:
                yield from self.use_ability(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action.attack, state)
            player = current_player(state)

            # this pokemon shuffle into deck(left)
            cards = type(action.source)() + self.attachment
            player.left.extend(cards)

            # choose another pokemon onto active spot
            tips = "You used the attack Aqua Return. You should choose 1 of your benched Pokemon and switch it onto active spot."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, player.bench, tips=tips, source=self
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            chosen_card = chosen_card[0]

            player.bench.remove(chosen_card)
            move_pokemon(player, chosen_card)

            shuffle_cards(player.left)
            auto_end_turn(state)

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")
