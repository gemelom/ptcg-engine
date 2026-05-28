from ptcg.core.ability import ActiveAbility
from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardType,
    PokemonRule,
    PokemonType,
    Stage,
)
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class BRS121Bibarel(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "BRS"
        self.number = "121"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Bibarel"
        self.hp = 120
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Bidoof"]
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Tail Smash",
                    "damage": 100,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS],
                    "text": "Flip a coin. If tails, this attack does nothing.",
                }
            )
        ]

        self.ability = [
            ActiveAbility(
                {
                    "name": "Industrious Incisors",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may draw cards until you have 5 cards in your hand.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        # attacks
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        # abilities
        player = current_player(state)
        if not player.onceUsedTurn[self.ability[0].name]:
            actions.extend(self.use_ability(state))

        return actions

    def use_ability(self, state):  # someone haven't finished it yet
        player = current_player(state)
        return [UseAbilityAction(player.id, self, self.ability[0])]

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
            # reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            if flip_coin(state) == Coin.HEAD:
                yield from reduce_attack_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            hand_cnt = len(player.hand)
            if hand_cnt < 5:
                draw_cnt = 5 - hand_cnt
                move_cards(
                    player.left[:draw_cnt],
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

            player.onceUsedTurn[action.ability.name] = True

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")
