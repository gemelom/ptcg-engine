from ptcg.core.ability import PassiveAbility
from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityTrigger,
    AbilityType,
    CardType,
    EnergyType,
    PokemonRule,
    PokemonType,
    Stage,
    SuperType,
)
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class PAR126Jirachi(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAR"
        self.number = "126"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Jirachi"
        self.hp = 70
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.METAL
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.FIRE]
        self.resistance = [CardType.GRASS]
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Charge Energy",
                    "damage": 0,
                    "cost": [CardType.COLORLESS],
                    "text": "Search your deck for up to 2 Basic Energy cards, reveal them, and put them into your hand. Then, shuffle your deck.",
                }
            )
        ]

        self.ability = [
            PassiveAbility(
                {
                    "name": "Stellar Veil",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKED,
                    "onceUsedPerTurn": False,
                    "text": "Prevent all damage counters from being placed on your Benched Pokemon "
                    "by effects of attacks used by your opponent's Basic Pokemon.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        return actions

    def use_ability(self, action, state):
        if isinstance(action, EffectAction):
            source = action.source
            target = action.target
            if (
                source.superType == SuperType.POKEMON
                and source.stage == Stage.BASIC
                and target in opponent_bench(state)
            ):
                action.effect.damage = 0

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            player = current_player(state)
            cards = [
                card
                for card in player.left
                if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
            ]

            tips = "You used the attack Charge Energy. You can choose up to 2 Basic Energy cards, and put them into your hand."
            actions = choose_card_actions(player.id, player.id, 0, 2, cards, tips=tips, source=self)

            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.left for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

            shuffle_cards(player.left)
            auto_end_turn(state)

        else:
            raise ValueError(f"Invalid action: {action}")
