from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    EvolvePokemonAction,
    UseAbilityAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_evolve_pokemon_action,
)
from ptcg.utils.utils import check_energy, current_player, move_cards, opponent_active
from ptcg.core.enums import CardPosition


class SIT068Kirlia(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Kirlia"
        self.set_name = "SIT"
        self.number = "068"
        self.id = f"{self.set_name}-{self.number}"

        self.hp = 80
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.PSYCHIC

        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.METAL]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []
        self.evolved = []
        self.evolveFrom = ["Ralts"]

        self.attacks = [
            Attack(
                {
                    "name": "Slap",
                    "damage": 30,
                    "cost": [CardType.PSYCHIC, CardType.COLORLESS],
                    "text": "",
                }
            )
        ]

        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Refinement",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may discard a card from your hand. If you do, draw 2 cards.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        player = current_player(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))

        if (
            not self.abilityUsed
            and not player.onceUsedTurn.get(self.ability[0].name, False)
            and len(player.hand) > 1
        ):
            actions.append(UseAbilityAction(state.turn, self, self.ability[0]))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)

            discard_candidates = [c for c in player.hand if c is not self]
            tips = "You used Refinement. Choose 1 card from your hand to discard."
            actions = choose_card_actions(
                player.id, player.id, 1, 1, discard_candidates, tips=tips, source=self
            )
            chosen = yield from reduce_choose_card_actions(actions, state)

            if chosen:
                move_cards(
                    chosen[0],
                    (player.id, CardPosition.HAND),
                    (player.id, CardPosition.DISCARD),
                    state,
                )

            draw = player.left[:2]
            move_cards(
                draw,
                (player.id, CardPosition.LEFT),
                (player.id, CardPosition.HAND),
                state,
            )

            self.abilityUsed = True
            player.onceUsedTurn[self.ability[0].name] = True
