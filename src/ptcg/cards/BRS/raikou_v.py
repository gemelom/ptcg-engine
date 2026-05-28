from ptcg.core.ability import ActiveAbility
from ptcg.core.action import AttackAction, PlayPokemonAction, UseAbilityAction
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
from ptcg.core.reducer import reduce_attack_action, reduce_play_pokemon_action
from ptcg.utils.utils import (
    check_energy,
    current_bench,
    current_player,
    move_cards,
    opponent_active,
    opponent_player,
)


class BRS048RaikouV(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Raikou V"
        self.set_name = "BRS"
        self.number = "048"
        self.id = f"{self.set_name}-{self.number}"

        # Pokémon attributes
        self.hp = 200
        self.pokemonType = PokemonType.V
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING

        # Retreat/Weakness/Resistance
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 2

        # List initialization
        self.energy = []
        self.attachment = []
        self.evolved = []

        # Attack definition
        self.attacks = [
            Attack(
                {
                    "name": "Lightning Rondo",
                    "damage": 20,
                    "cost": [CardType.LIGHTNING, CardType.COLORLESS],
                    "text": "This attack does 20 more damage for each Benched Pokémon (both yours and your opponent's).",
                }
            )
        ]

        # Ability definition
        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Fleet-Footed",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, if this Pokémon is in Active Spot, you may draw a card.",
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

        # Fleet-Footed ability - only when in active spot
        for ability in self.ability:
            if (
                not self.abilityUsed
                and not player.onceUsedTurn[ability.name]
                and self.position == PokemonPosition.ACTIVE
            ):
                actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        """Handle action execution"""
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, UseAbilityAction):
            self._fleet_footed_ability(action, state)
        elif isinstance(action, AttackAction):
            yield from self._lightning_rondo_attack(action, state)

    def _fleet_footed_ability(self, action, state):
        """Fleet-Footed: Draw a card when in active spot"""
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

        # Mark ability as used
        self.abilityUsed = True
        player.onceUsedTurn[action.ability.name] = True

    def _lightning_rondo_attack(self, action, state):
        """Lightning Rondo: +20 damage for each benched Pokémon"""
        opp = opponent_player(state)

        # Calculate bonus damage: 20 for each benched Pokémon (both players)
        total_bench = len(current_bench(state)) + len(opp.bench)
        bonus_damage = total_bench * 20

        # Set attack damage
        action.attack.damage = 20 + bonus_damage

        yield from reduce_attack_action(action, state)
