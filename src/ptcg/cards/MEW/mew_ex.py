from ptcg.core.ability import ActiveAbility
from ptcg.core.action import AttackAction, PlayPokemonAction, UseAbilityAction, choose_card_actions
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
    reduce_play_pokemon_action,
)
from ptcg.utils.utils import (
    check_energy,
    current_player,
    move_cards,
    opponent_active,
    opponent_player,
)


class MEW151MewEX(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "MEW"
        self.number = "151"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Mew ex"
        self.hp = 180
        self.pokemonType = PokemonType.EX
        self.cardType = CardType.PSYCHIC
        self.stage = Stage.BASIC
        self.pokemonRule = PokemonRule.NONE
        self.weakness = [CardType.DARK]
        self.resistance = [CardType.FIGHTING]
        self.retreat = []
        self.prize = 2

        self.energy = []
        self.attachment = []

        # Ability
        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Restart",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may draw cards until you have 3 cards in your hand.",
                }
            )
        ]

        # Attack
        self.attacks = [
            Attack(
                {
                    "name": "Genome Hacking",
                    "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS],
                    "damage": 0,  # Variable damage based on copied attack
                    "text": "Choose 1 of your opponent's Active Pokémon's attacks and use it as this attack.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        # Attack actions
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        # Ability actions
        for ability in self.ability:
            if not self.abilityUsed and not current_player(state).onceUsedTurn[ability.name]:
                actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)

            # Restart ability: draw cards until you have 3 cards in hand
            cards_needed = max(0, 3 - len(player.hand))
            if cards_needed > 0 and len(player.left) > 0:
                draw_cards = player.left[: min(cards_needed, len(player.left))]
                move_cards(
                    draw_cards,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

            # Mark ability as used
            self.abilityUsed = True
            player.onceUsedTurn[action.ability.name] = True

        elif isinstance(action, AttackAction):
            # Genome Hacking attack
            if action.attack.name == "Genome Hacking":
                yield from self._genome_hacking_attack(action, state)
            else:
                yield from reduce_attack_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")

    def _genome_hacking_attack(self, action, state):
        """Handle the Genome Hacking attack"""
        player = current_player(state)
        opponent = opponent_player(state)

        # Get opponent's active Pokemon
        if not opponent.active:
            # No opponent active Pokemon, attack fails
            yield from reduce_attack_action(action, state)
            return

        opponent_active_pokemon = opponent.active[0]

        # Get available attacks from opponent's active Pokemon
        available_attacks = []
        if hasattr(opponent_active_pokemon, "attacks") and opponent_active_pokemon.attacks:
            available_attacks = opponent_active_pokemon.attacks

        if not available_attacks:
            # No attacks available to copy, attack fails
            yield from reduce_attack_action(action, state)
            return

        # Choose which attack to copy
        tips = f"You used Genome Hacking. Choose 1 of {opponent_active_pokemon.name}'s attacks to copy."
        actions = choose_card_actions(
            player.id, player.id, 1, 1, available_attacks, tips=tips, source=self
        )
        chosen_attack = yield from reduce_choose_card_actions(actions, state)
        chosen_attack = chosen_attack[0]

        # Create a new attack action with the copied attack
        copied_attack = Attack(
            {
                "name": chosen_attack.name,
                "cost": action.attack.cost,  # Use original Genome Hacking cost
                "damage": chosen_attack.damage,
                "text": f"Copied from {opponent_active_pokemon.name}: {chosen_attack.text}",
            }
        )

        # Create new attack action with copied attack
        genome_attack_action = AttackAction(action.playerId, self, copied_attack, action.target)

        # If the copied attack has special effects, we need to handle them
        # For now, we'll just do the basic damage
        yield from reduce_attack_action(genome_attack_action, state)
