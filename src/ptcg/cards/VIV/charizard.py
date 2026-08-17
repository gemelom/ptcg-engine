from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    EvolvePokemonAction,
    RetreatAction,
    UseAbilityAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardPosition,
    CardType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
)
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_evolve_pokemon_action,
    reduce_retreat_action,
)
from ptcg.utils.utils import check_energy, current_player, move_cards, opponent_active


class VIV025Charizard(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "VIV"
        self.number = "025"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Charizard"
        self.hp = 170
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.FIRE
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.WATER]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []
        self.evolveFrom = ["Charmeleon", "Charmander"]
        self.evolved = []
        self.attacks = [
            Attack(
                {
                    "name": "Royal Blaze",
                    "damage": 100,
                    "cost": [CardType.FIRE, CardType.FIRE],
                    "text": "This attack does 50 more damage for each Leon card in your "
                    "discard pile.",
                }
            )
        ]

        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Battle Sense",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may look at the top 3 cards of your "
                    "deck and put 1 of them into your hand. Discard the other cards.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        player = current_player(state)

        if self.position == PokemonPosition.ACTIVE:
            targets = opponent_active(state)
            actions.extend(
                AttackAction(state.turn, self, attack, target)
                for attack in self.attacks
                if check_energy(attack.cost, self.energy)
                for target in targets
            )

        if not self.abilityUsed and player.left:
            actions.append(UseAbilityAction(state.turn, self, self.ability[0]))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            player = current_player(state)
            leon_count = sum(card.name == "Leon" for card in player.discard)
            action.attack.damage += 50 * leon_count
            yield from reduce_attack_action(action, state)
        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            look_cards = list(player.left[:3])
            choices = choose_card_actions(
                player.id,
                player.id,
                1,
                1,
                look_cards,
                hidden=True,
                tips="You used Battle Sense. Choose 1 card to put into your hand; "
                "discard the others.",
                source=self,
            )
            chosen_cards = yield from reduce_choose_card_actions(choices, state)

            move_cards(
                chosen_cards,
                (player.id, CardPosition.LEFT),
                (player.id, CardPosition.HAND),
                state,
            )
            unchosen_cards = [card for card in look_cards if card not in chosen_cards]
            if unchosen_cards:
                move_cards(
                    unchosen_cards,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.DISCARD),
                    state,
                )
            self.abilityUsed = True
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
