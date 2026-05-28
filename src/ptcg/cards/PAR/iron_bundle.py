from ptcg.core.ability import ActiveAbility
from ptcg.core.action import AttackAction, PlayPokemonAction, UseAbilityAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
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
    discard_pokemon,
    move_pokemon,
    opponent_active,
    opponent_player,
)


class PAR056IronBundle(PokemonCard):
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "056"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Iron Bundle"
        self.hp = 100
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Refrigerated Stream",
                    "damage": 80,
                    "cost": [CardType.WATER, CardType.COLORLESS, CardType.COLORLESS],
                    "text": "If the Defending Pokémon is an Evolution Pokémon, it can't attack during your opponent's next turn.",
                }
            )
        ]

        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Hyper Blower",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, if this Pokémon is on your Bench, you may switch out your opponent's Active Pokémon to the Bench. (Your opponent chooses the new Active Pokémon.) If you do, discard this Pokémon and all attached cards.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        opponent = opponent_player(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        AttackAction(state.turn, self, attack, target)
                        for target in opponent_active(state)
                    )

        bench_size = getattr(opponent, "benchSize", 5)
        if (
            self.position == PokemonPosition.BENCH
            and not self.abilityUsed
            and not player.onceUsedTurn.get(self.ability[0].name, False)
            and 0 < len(opponent.bench) < bench_size
        ):
            actions.append(UseAbilityAction(state.turn, self, self.ability[0]))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            opponent = opponent_player(state)

            # Force opponent's active to bench
            former_active = opponent.active[0]
            move_pokemon(opponent, former_active)

            # Opponent chooses new active from bench
            tips = (
                "Iron Bundle's Hyper Blower: Your Active Pokémon was switched to the Bench. "
                "Choose 1 of your Benched Pokémon to be your new Active Pokémon."
            )
            bench_actions = choose_card_actions(
                opponent.id, opponent.id, 1, 1, opponent.bench, tips=tips, source=self
            )
            chosen = yield from reduce_choose_card_actions(bench_actions, state)
            move_pokemon(opponent, chosen[0])

            # Discard Iron Bundle and its attachments
            discard_pokemon(player, self)

            self.abilityUsed = True
            player.onceUsedTurn[action.ability.name] = True

    def reset_turn_stats(self):
        self.abilityUsed = False
