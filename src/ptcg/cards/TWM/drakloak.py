from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    EvolvePokemonAction,
    UseAbilityAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_evolve_pokemon_action,
)
from ptcg.utils.utils import check_energy, current_player, move_cards, opponent_active


class TWM129Drakloak(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TWM"
        self.number = "129"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Drakloak"
        self.hp = 90
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS]
        self.weakness = []
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Dreepy"]
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Dragon Headbutt",
                    "damage": 70,
                    "cost": [CardType.FIRE, CardType.PSYCHIC],
                    "text": "",
                }
            )
        ]

        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Recon Directive",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": False,
                    "text": "Once during your turn, you may look at the top 2 "
                    "cards of your deck and put 1 of them into your hand. "
                    "Put the other card on the bottom of your deck.",
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
                actions.extend([UseAbilityAction(state.turn, self, ability)])
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            # Look at top 2 cards of deck (index 0 is top)
            look_cards = player.left[:2]

            tips = "You used the ability Recon Directive. You should choose 1 of two given cards and put it into your hand. Then, put the other card on the bottom of your deck."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, look_cards, tips=tips, source=self
            )
            chosen_cards = yield from reduce_choose_card_actions(actions, state)

            if chosen_cards and all(card in player.left for card in chosen_cards):
                move_cards(
                    chosen_cards,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )
                # Move unchosen card to bottom of deck
                for card in look_cards:
                    if card not in chosen_cards and card in player.left:
                        player.left.remove(card)
                        player.left.append(card)
                        for idx, c in enumerate(player.left):
                            c.index = idx + 1

            self.abilityUsed = True
