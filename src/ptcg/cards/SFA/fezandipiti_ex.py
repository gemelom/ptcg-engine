from ptcg.core.ability import ActiveAbility
from ptcg.core.action import AttackAction, EffectAction, PlayPokemonAction, UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.effect import Effect
from ptcg.core.enums import AbilityType, CardType, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class SFA092FezandipitiEX(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SFA"
        self.number = "092"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Fezandipiti ex"
        self.hp = 210
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.DARK
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 2

        self.energy = []
        self.attachment = []

        self.evolveFrom = []
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Cruel Arrow",
                    "damage": 100,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS],
                    "text": "This attack does 100 damage to 1 of your opponent's Pokémon. "
                    "(Don't apply Weakness and Resistance for Benched Pokémon.)",
                }
            )
        ]

        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Flip the Script",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, if any of your Pokémon were Knocked "
                    "Out during your opponent's last turn, you may draw 3 cards. You "
                    "can't use more than 1 Flip the Script Ability each turn.",
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

        player = current_player(state)
        for ability in self.ability:
            if (
                not self.abilityUsed
                and not player.onceUsedTurn.get(ability.name, False)
                and player.hasPokemonDead
            ):
                actions.extend([UseAbilityAction(state.turn, self, ability)])

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            player = current_player(state)
            opponent = opponent_player(state)

            tips = (
                "You used the attack Cruel Arrow. You may choose 1 of your opponent's "
                "Pokemon and put 10 damage counter on it."
            )
            actions = choose_card_actions(
                player.id,
                opponent.id,
                1,
                1,
                opponent_all_pokemon(state),
                tips=tips,
                source=self,
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            chosen_card = chosen_card[0]

            effect = Effect(10)
            yield from reduce_effect_action(
                EffectAction(player.id, self, effect, chosen_card), state
            )
            auto_end_turn(state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            draw_cards = player.left[:3]
            move_cards(
                draw_cards, (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state
            )

            # Mark ability as used
            self.abilityUsed = True
            player.onceUsedTurn[action.ability.name] = True
