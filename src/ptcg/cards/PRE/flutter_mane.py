from ptcg.core.ability import PassiveAbility
from ptcg.core.action import (
    AttackAction,
    EffectAction,
    PlayPokemonAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.effect import Effect
from ptcg.core.enums import (
    AbilityTrigger,
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
    reduce_effect_action,
    reduce_play_pokemon_action,
)
from ptcg.utils.utils import (
    auto_end_turn,
    check_energy,
    current_player,
    opponent_active,
    opponent_bench,
    opponent_player,
)


class PRE043FlutterMane(PokemonCard):
    """Flutter Mane - PRE 043"""

    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PRE"
        self.number = "043"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Flutter Mane"
        self.hp = 90
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC

        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.METAL]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []
        self.evolveFrom = []
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Hex Hurl",
                    "damage": 90,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS],
                    "text": "Put 2 damage counters on your opponent's Benched Pokémon in any way you like.",
                }
            )
        ]

        midnight_fluttering = PassiveAbility(
            {
                "name": "Midnight Fluttering",
                "abilityType": AbilityType.PASSIVE_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": False,
                "text": "As long as this Pokémon is in the Active Spot, your opponent's Active Pokémon has no Abilities, except for Midnight Fluttering.",
            }
        )
        # Flag checked by player.py and ability_handler.py to suppress opponent active abilities
        midnight_fluttering.suppresses_opponent_active_abilities = True
        self.ability = [midnight_fluttering]

    def get_actions(self, state):
        actions = []
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [
                            AttackAction(state.turn, self, attack, target)
                            for target in opponent_active(state)
                        ]
                    )
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            player = current_player(state)
            opponent = opponent_player(state)

            yield from reduce_attack_action(action, state, auto_end_turn=False)

            # Place 2 damage counters on opponent's Benched Pokémon
            effect = Effect(1)
            for _ in range(2):
                bench = opponent_bench(state)
                if bench:
                    tips = "You used Hex Hurl. Choose 1 of your opponent's Benched Pokémon to place 1 damage counter on."
                    actions = choose_card_actions(
                        player.id, opponent.id, 1, 1, bench, tips=tips, source=self
                    )
                    chosen = yield from reduce_choose_card_actions(actions, state)
                    if chosen:
                        yield from reduce_effect_action(
                            EffectAction(player.id, self, effect, chosen[0]), state
                        )

            auto_end_turn(state)
