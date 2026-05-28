from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    EvolvePokemonAction,
    UseAbilityAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.effect import *
from ptcg.core.enums import AbilityType, CardType, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class OBF164PidgeotEX(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "OBF"
        self.number = "164"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Pidgeot ex"
        self.hp = 280
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.COLORLESS
        self.retreat = []
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.prize = 2

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Pidgeotto", "Pidgey"]
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Blustery Wind",
                    "damage": 120,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS],
                    "text": "You may discard a Stadium in play.",
                }
            )
        ]

        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Quick Search",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may search your deck for a card and put it into your hand. "
                    "Then, shuffle your deck. You can't use more than 1 Quick Search Ability each turn.",
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

        for ability in self.ability:
            if not self.abilityUsed and not current_player(state).onceUsedTurn[ability.name]:
                actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            cards = player.left
            tips = "You used the ability Quick Search. You can choose up to 1 card from your deck and put it into your hand."
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
            # once used each turn
            self.abilityUsed = True
            player.onceUsedTurn[action.ability.name] = True
