from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    EvolvePokemonAction,
    PlayPokemonAction,
    RetreatAction,
    UseAbilityAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardPosition,
    CardTag,
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
    reduce_play_pokemon_action,
    reduce_retreat_action,
)
from ptcg.utils.utils import (
    check_energy,
    current_player,
    opponent_active,
)


class SIT139LugiaVSTAR(PokemonCard):
    """
    Lugia VSTAR - Silver Tempest 139

    HP: 280 | Colorless | Basic VSTAR

    Ability: Summoning Star (VSTAR Power)
    - You can use this ability only once during your turn.
    - Put up to 2 Colorless Pokémon from your discard pile onto your Bench.

    Attack: Tempest Dive (130 damage, 4 Colorless)

    Evolution: Evolves from Lugia V
    Prize: 2 (V rule box)
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SIT"
        self.number = "139"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Lugia VSTAR"
        self.hp = 280
        self.pokemonType = PokemonType.VSTAR
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.prize = 2
        self.cardTag = CardTag.VSTAR

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Lugia V"]  # Evolves from Lugia V

        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Tempest Dive",
                    "damage": 130,
                    "cost": [
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                    ],
                    "text": "",
                }
            )
        ]

        self.ability = [
            ActiveAbility(
                {
                    "name": "Summoning Star",
                    "abilityType": AbilityType.ACTIVE_ABILITY,  # VSTAR Power - once per game
                    "onceUsedPerTurn": False,
                    "text": "You can use this ability only once during your turn. "
                    "Put up to 2 Colorless Pokémon from your discard pile onto your Bench.",
                }
            )
        ]

    def get_actions(self, state):
        """
        Get all available actions for Lugia VSTAR.

        Returns:
            List of valid actions the player can take with this card.
        """
        actions = []
        player = current_player(state)
        targets = opponent_active(state)

        # Attack actions (when active and has energy)
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        # VSTAR ability action (when in play and VSTAR not yet used)
        if self.position in [PokemonPosition.ACTIVE, PokemonPosition.BENCH]:
            # Check if VSTAR power hasn't been used this game
            if player.onceUsedGame.get(CardTag.VSTAR) is False:
                # Check if there are valid targets in discard
                valid_discard = [
                    card for card in player.discard if self._is_valid_colorless_pokemon(card)
                ]
                if len(valid_discard) > 0 and len(player.bench) < 5:
                    for ability in self.ability:
                        actions.append(UseAbilityAction(player.id, self, ability))

        return actions

    def _is_valid_colorless_pokemon(self, card) -> bool:
        """
        Check if a card is a valid Colorless Pokémon for Summoning Star.

        Args:
            card: The card to check.

        Returns:
            True if the card is a Colorless Pokémon that can be put on the bench.
        """
        if not isinstance(card, PokemonCard):
            return False
        if card.cardType != CardType.COLORLESS:
            return False
        # Can only put Basic or Stage 1 Pokémon on bench
        if card.stage not in [Stage.BASIC, Stage.STAGE_1]:
            return False
        return True

    def reduce_action(self, action, state):
        """
        Process actions for Lugia VSTAR.

        Args:
            action: The action to process.
            state: Current game state.

        Yields:
            State updates during action processing.
        """
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            if action.attack == self.attacks[0]:
                # Tempest Dive - standard attack
                yield from reduce_attack_action(action, state)
            else:
                raise ValueError(f"Invalid attack: {action.attack}")

        elif isinstance(action, UseAbilityAction):
            yield from self._use_summoning_star(action, state)

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")

    def _use_summoning_star(self, action, state):
        """
        Use the Summoning Star VSTAR ability.

        Put up to 2 Colorless Pokémon from discard pile onto Bench.
        This can only be used once per game.

        Args:
            action: The UseAbilityAction.
            state: Current game state.

        Yields:
            State updates during ability processing.
        """
        player = current_player(state)

        # Get valid Colorless Pokémon from discard
        valid_discard = [card for card in player.discard if self._is_valid_colorless_pokemon(card)]

        # Calculate how many we can actually put on bench
        bench_space = 5 - len(player.bench)
        max_to_put = min(2, bench_space, len(valid_discard))

        if max_to_put == 0:
            return  # No valid targets or no bench space

        tips = (
            f"You used the VSTAR Power Summoning Star. "
            f"Choose up to {max_to_put} Colorless Pokémon from your discard pile to put onto your Bench."
        )

        actions = choose_card_actions(
            player.id, player.id, 0, max_to_put, valid_discard, tips=tips, source=self
        )

        chosen_cards = yield from reduce_choose_card_actions(actions, state)

        # Move chosen cards from discard to bench
        for card in chosen_cards:
            # Create a fresh copy for the bench
            new_pokemon = type(card)()
            new_pokemon.cardPosition = CardPosition.BENCH
            new_pokemon.position = PokemonPosition.BENCH
            new_pokemon.index = len(player.bench) + 1
            player.bench.append(new_pokemon)

        # Remove from discard
        for card in chosen_cards:
            player.discard.remove(card)

        # Mark VSTAR as used for this game
        player.onceUsedGame[CardTag.VSTAR] = True

        # Re-index discard pile
        for idx, card in enumerate(player.discard):
            card.index = idx + 1
