from ptcg.core.ability import PassiveAbility
from ptcg.core.action import AttackAction, EffectAction, EvolvePokemonAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.effect import Effect
from ptcg.core.enums import *
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_effect_action,
    reduce_evolve_pokemon_action,
)
from ptcg.utils.utils import (
    auto_end_turn,
    check_energy,
    current_player,
    opponent_active,
    opponent_player,
)


class TWM200DragapultEX(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TWM"
        self.number = "200"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Dragapult ex"
        self.hp = 320
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.TERA
        self.stage = Stage.STAGE_2
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS]
        self.weakness = []
        self.resistance = []
        self.prize = 2

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {"name": "Jet Headbutt", "damage": 70, "cost": [CardType.COLORLESS], "text": ""}
            ),
            Attack(
                {
                    "name": "Phantom Dive",
                    "damage": 200,
                    "cost": [CardType.FIRE, CardType.PSYCHIC],
                    "text": "Put 6 damage counters on your opponent's Benched Pokémon in any way you like.",
                }
            ),
        ]

        self.ability = [
            PassiveAbility(
                {
                    "name": "Tera",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKED,
                    "onceUsedPerTurn": True,
                    "text": "As long as this Pokémon is on your Bench, prevent all damage done to this Pokémon "
                    "by attacks (both yours and your opponent's).",
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

        return actions

    def use_ability(self, action, state):
        if isinstance(action, AttackAction):
            if self.position == PokemonPosition.BENCH and action.target == self:
                action.attack.damage = 0

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            if action.attack == self.attacks[0]:
                yield from reduce_attack_action(action, state)

            elif action.attack == self.attacks[1]:
                player = current_player(state)
                opponent = opponent_player(state)

                yield from reduce_attack_action(action, state)

                # reduce put dc effect
                effect = Effect(1)
                for _ in range(6):
                    if len(opponent.bench) > 0:
                        tips = "You used the attack Phantom Dive. You may choose 1 of your opponent's benched Pokemon and put 1 damage counter on it."
                        actions = choose_card_actions(
                            player.id, opponent.id, 1, 1, opponent.bench, tips=tips
                        )
                        chosen_card = yield from reduce_choose_card_actions(actions, state)
                        if chosen_card:
                            yield from reduce_effect_action(
                                EffectAction(player.id, self, effect, chosen_card[0]), state
                            )

                auto_end_turn(state)
