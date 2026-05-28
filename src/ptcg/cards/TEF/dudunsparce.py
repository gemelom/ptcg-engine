from ptcg.core.ability import ActiveAbility
from ptcg.core.action import AttackAction, EvolvePokemonAction, UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import *
from ptcg.core.reducer import _force_active_replacement, reduce_attack_action, reduce_evolve_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_player,
    move_cards,
    opponent_active,
    shuffle_cards,
)


class TEF129Dudunsparce(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Dudunsparce"
        self.set_name = "TEF"
        self.number = "129"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 140
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.COLORLESS

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 2

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.evolveFrom = ["Dunsparce"]

        # Attack definition
        self.attacks = [
            Attack(
                {
                    "name": "Land Crush",
                    "damage": 90,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS],
                    "text": "",
                }
            )
        ]

        # Ability definition
        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Run Away Draw",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may draw 3 cards. If you drew any cards in this way, shuffle this Pokémon and all attached cards into your deck.",
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

        # Run Away Draw ability
        for ability in self.ability:
            if not self.abilityUsed and not player.onceUsedTurn[ability.name]:
                actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, UseAbilityAction):
            yield from self._run_away_draw_ability(action, state)
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)

    def _run_away_draw_ability(self, action, state):
        """Run Away Draw: Draw 3 cards, then shuffle this card and attachments into deck"""
        player = current_player(state)

        was_active = self.position == PokemonPosition.ACTIVE
        bench_has_pokemon = len(player.bench) > 0

        # Can only shuffle self if there's somewhere else to be (active has another, or bench exists)
        can_shuffle = bench_has_pokemon or (not was_active and player.active)
        if not can_shuffle:
            self.abilityUsed = True
            player.onceUsedTurn[action.ability.name] = True
            return

        # Draw 3 cards
        cards_to_draw = min(3, len(player.left))
        if cards_to_draw > 0:
            draw_cards = player.left[:cards_to_draw]
            move_cards(
                draw_cards,
                (player.id, CardPosition.LEFT),
                (player.id, CardPosition.HAND),
                state,
            )

        # Remove from play area and update bench indices
        if was_active:
            player.active.remove(self)
        else:
            player.bench.remove(self)
            for idx, card in enumerate(player.bench):
                card.index = idx + 1

        # Shuffle this Pokémon and all attached cards (energy + tools) into deck
        cards_to_shuffle = [self] + list(self.attachment)
        for card in cards_to_shuffle:
            card.cardPosition = CardPosition.LEFT
        player.left.extend(cards_to_shuffle)

        self.position = None
        self.energy = []
        self.attachment = []

        shuffle_cards(player.left)

        # If was active, force player to choose a bench replacement
        if was_active and bench_has_pokemon:
            yield from _force_active_replacement(player, state, state.turn)

        self.abilityUsed = True
        player.onceUsedTurn[action.ability.name] = True
