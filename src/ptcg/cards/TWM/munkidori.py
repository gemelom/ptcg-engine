from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    EffectAction,
    PlayPokemonAction,
    UseAbilityAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.effect import Effect
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_effect_action,
    reduce_play_pokemon_action,
)
from ptcg.utils.utils import (
    check_energy,
    current_all_pokemon,
    current_player,
    opponent_active,
    opponent_all_pokemon,
    opponent_player,
)


class TWM095Munkidori(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Munkidori"
        self.set_name = "TWM"
        self.number = "095"
        self.id = f"{self.set_name}-{self.number}"

        self.hp = 110
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC

        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.DARK]
        self.resistance = [CardType.FIGHTING]
        self.prize = 1

        self.energy = []
        self.attachment = []
        self.evolved = []
        self.evolveFrom = []

        self.attacks = [
            Attack(
                {
                    "name": "Mind Bend",
                    "damage": 60,
                    "cost": [CardType.PSYCHIC, CardType.COLORLESS],
                    "text": "Your opponent's Active Pokémon is now Confused.",
                }
            )
        ]

        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Adrena-Brain",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, if this Pokémon has any Darkness Energy attached, "
                    "you may move up to 3 damage counters from 1 of your Pokémon to 1 of your opponent's Pokémon.",
                }
            )
        ]

    def _has_darkness_energy(self):
        return CardType.DARK in self.energy

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
            and self._has_darkness_energy()
            and opponent_all_pokemon(state)
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

            my_pokemon = current_all_pokemon(state)
            tips = "You used Adrena-Brain. Choose 1 of your Pokémon to move damage counters from."
            source_actions = choose_card_actions(
                player.id, player.id, 1, 1, my_pokemon, tips=tips, source=self
            )
            source_chosen = yield from reduce_choose_card_actions(source_actions, state)
            source = source_chosen[0]

            opp_pokemon = opponent_all_pokemon(state)
            tips = "Choose 1 of your opponent's Pokémon to move up to 3 damage counters onto."
            target_actions = choose_card_actions(
                player.id, player.id, 1, 1, opp_pokemon, tips=tips, source=self
            )
            target_chosen = yield from reduce_choose_card_actions(target_actions, state)
            target = target_chosen[0]

            # Move up to 3 damage counters (each = 10 HP)
            counters_to_move = min(3, (source.hp // 10))
            source.hp += counters_to_move * 10

            opp = opponent_player(state)
            effect = Effect(1)
            for _ in range(counters_to_move):
                in_play = opp.active + opp.bench
                if target.hp <= 0 or target not in in_play:
                    break
                yield from reduce_effect_action(
                    EffectAction(player.id, self, effect, target), state
                )

            self.abilityUsed = True
            player.onceUsedTurn[self.ability[0].name] = True
