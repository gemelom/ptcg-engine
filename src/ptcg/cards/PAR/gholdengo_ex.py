from ptcg.core.ability import ActiveAbility
from ptcg.core.action import AttackAction, EvolvePokemonAction, UseAbilityAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardPosition,
    CardType,
    EnergyType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
    SuperType,
)
from ptcg.core.reducer import reduce_attack_action, reduce_choose_card_actions, reduce_evolve_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_player,
    move_cards,
    opponent_active,
)


class PAR139Gholdengoex(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Gholdengo ex"
        self.set_name = "PAR"
        self.number = "139"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 260
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.METAL

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.FIRE]
        self.resistance = [CardType.GRASS]
        self.prize = 2

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.evolveFrom = ["Gimmighoul"]

        # Attack definition
        self.attacks = [
            Attack(
                {
                    "name": "Make It Rain",
                    "damage": 0,
                    "cost": [CardType.METAL],
                    "text": "Discard any number of Basic Energy cards from your hand. This attack does 50 damage for each card you discarded in this way.",
                }
            )
        ]

        # Ability definition
        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Coin Bonus",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may draw a card. If this Pokémon is in the Active Spot, draw 1 more card.",
                }
            )
        ]

    def get_actions(self, state):
        """Return list of currently available actions"""
        actions = []
        player = current_player(state)

        # If in active position, check if can attack
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))

        # Coin Bonus ability
        for ability in self.ability:
            if not self.abilityUsed and not player.onceUsedTurn[ability.name]:
                actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, UseAbilityAction):
            self._coin_bonus_ability(action, state)
        elif isinstance(action, AttackAction):
            yield from self._make_it_rain_attack(action, state)

    def _coin_bonus_ability(self, action, state):
        """Coin Bonus: Draw 1-2 cards depending on position"""
        player = current_player(state)

        # Draw 1 card
        cards_to_draw = min(1, len(player.left))
        if cards_to_draw > 0:
            draw_cards = player.left[:cards_to_draw]
            move_cards(
                draw_cards,
                (player.id, CardPosition.LEFT),
                (player.id, CardPosition.HAND),
                state,
            )

        # If in active spot, draw 1 more card
        if self.position == PokemonPosition.ACTIVE:
            cards_to_draw = min(1, len(player.left))
            if cards_to_draw > 0:
                draw_cards = player.left[:cards_to_draw]
                move_cards(
                    draw_cards,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

        # Mark ability as used
        self.abilityUsed = True
        player.onceUsedTurn[action.ability.name] = True

    def _make_it_rain_attack(self, action, state):
        """Make It Rain: Discard any number of basic energy from hand, 50 damage per card discarded"""
        player = current_player(state)

        basic_energy = [
            card
            for card in player.hand
            if card.superType == SuperType.ENERGY and card.energyType == EnergyType.BASIC
        ]

        if basic_energy:
            tips = "Make It Rain: choose any number of Basic Energy cards from your hand to discard. This attack does 50 damage for each card discarded."
            actions = choose_card_actions(
                player.id, player.id, 0, len(basic_energy), basic_energy, tips=tips, source=self
            )
            chosen = yield from reduce_choose_card_actions(actions, state)
            if chosen:
                move_cards(
                    chosen,
                    (player.id, CardPosition.HAND),
                    (player.id, CardPosition.DISCARD),
                    state,
                )
            action.attack.damage = 50 * len(chosen)
        else:
            action.attack.damage = 0

        yield from reduce_attack_action(action, state)
