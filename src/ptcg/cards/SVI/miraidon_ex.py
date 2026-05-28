from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    PlayPokemonAction,
    UseAbilityAction,
    choose_card_actions,
)
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
    SuperType,
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
    shuffle_cards,
)


class SVI253MiraidonEX(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SVI"
        self.number = "253"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Miraidon ex"
        self.hp = 220
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
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
                    "name": "Photon Blaster",
                    "damage": 220,
                    "cost": [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS],
                    "text": "During your next turn, this Pokémon can't attack.",
                }
            )
        ]

        self.abilityUsed = False
        self.useAttackLastTurn = False
        self.attackDisabledTurns = 0  # 用于跟踪攻击被禁用的回合数
        self.ability = [
            ActiveAbility(
                {
                    "name": "Tandem Unit",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may search your deck for up to 2 Basic [L] Pokémon and put them onto your Bench. Then, shuffle your deck.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        # 检查宝可梦是否可以攻击：必须是活跃位置、本回合未攻击过、且攻击未被禁用
        if (
            self.position == PokemonPosition.ACTIVE
            and not self.useAttackLastTurn
            and self.attackDisabledTurns <= 0
        ):
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        # Tandem Unit ability
        player = current_player(state)
        for ability in self.ability:
            if not self.abilityUsed and not player.onceUsedTurn[ability.name]:
                actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            # Mark that this Pokemon used attack last turn (can't attack next turn)
            self.useAttackLastTurn = True

            # 如果使用的是Photon Blaster，则设置攻击禁用2个回合
            if action.attack.name == "Photon Blaster":
                self.attackDisabledTurns = 2  # 禁用接下来的2个回合（包括当前回合结束后的一个回合）

            yield from reduce_attack_action(action, state)

        elif isinstance(action, UseAbilityAction):
            # Tandem Unit - search for up to 2 Basic Lightning Pokemon
            player = current_player(state)
            basic_lightning_pokemon = [
                card
                for card in player.left
                if card.superType == SuperType.POKEMON
                and card.stage == Stage.BASIC
                and card.cardType == CardType.LIGHTNING
            ]

            tips = "You used the ability Tandem Unit. You may choose up to 2 Basic Lightning Pokemon from your deck and put them onto your Bench."
            actions = choose_card_actions(
                player.id,
                player.id,
                0,
                min(len(basic_lightning_pokemon), 2),
                basic_lightning_pokemon,
                tips=tips,
                source=self,
            )

            chosen_cards = yield from reduce_choose_card_actions(actions, state)

            # Move chosen Pokemon to bench
            for pokemon in chosen_cards:
                if pokemon in player.left and len(player.bench) < player.benchSize:
                    # Move card from deck to bench using move_cards
                    move_cards(
                        pokemon,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.BENCH),
                        state,
                    )
                    # Set position attributes
                    pokemon.position = PokemonPosition.BENCH

            # Shuffle deck
            shuffle_cards(player.left)

            # Mark ability as used
            self.abilityUsed = True
            player.onceUsedTurn[action.ability.name] = True

    def reset_turn_stats(self):
        """Reset stats at the beginning of each turn"""
        self.abilityUsed = False
        # 减少攻击禁用回合数计数
        if self.attackDisabledTurns > 0:
            self.attackDisabledTurns -= 1
        # 注意：useAttackLastTurn在next_turn函数中被重置
        pass
