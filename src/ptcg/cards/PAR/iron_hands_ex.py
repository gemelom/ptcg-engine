from ptcg.core.action import AttackAction, PlayPokemonAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    CardPosition,
    CardType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
)
from ptcg.core.exceptions import GameTermination
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_play_pokemon_action,
)
from ptcg.utils.utils import (
    check_energy,
    current_player,
    discard_pokemon,
    move_cards,
    opponent_active,
    opponent_player,
)


class PAR248IronHandsEX(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAR"
        self.number = "248"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Iron Hands ex"
        self.hp = 230
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
        self.retreat = [
            CardType.COLORLESS,
            CardType.COLORLESS,
            CardType.COLORLESS,
            CardType.COLORLESS,
        ]
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
                    "name": "Arm Press",
                    "damage": 160,
                    "cost": [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS],
                    "text": "",
                }
            ),
            Attack(
                {
                    "name": "Amp You Very Much",
                    "damage": 120,
                    "cost": [
                        CardType.LIGHTNING,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                        CardType.COLORLESS,
                    ],
                    "text": "If your opponent's Pokémon is Knocked Out by damage from this attack, take 1 more Prize card.",
                }
            ),
        ]

        self.ability = []

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

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            if action.attack == self.attacks[0]:
                # Arm Press - normal attack
                yield from reduce_attack_action(action, state)
            elif action.attack == self.attacks[1]:
                # Amp You Very Much - attack with extra prize card effect
                yield from self._amp_you_very_much_attack(action, state)
            else:
                raise ValueError(f"Invalid attack: {action.attack}")

    def _amp_you_very_much_attack(self, action, state):
        """
        Custom implementation of Amp You Very Much attack that grants an extra prize card
        if the opponent's Pokemon is knocked out by this attack.
        """
        # Apply all passive abilities first (same as reduce_attack_action)
        from ptcg.core.ability import PassiveAbility
        from ptcg.core.enums import AbilityTrigger

        # passive ability
        if (
            hasattr(action.source, "ability")
            and isinstance(getattr(action.source, "ability"), PassiveAbility)
            and action.source.ability.abilityTrigger == AbilityTrigger.ATTACKING
        ):
            action.source.use_ability(action, state)

        for card in state.stadium:
            if (
                hasattr(card, "ability")
                and isinstance(getattr(card, "ability"), PassiveAbility)
                and card.ability.abilityTrigger == AbilityTrigger.ATTACKING
            ):
                card.use_ability(action, state)

        # Calculate damage
        damage = action.attack.damage

        # Apply weakness & resistance
        if action.source.cardType in action.target.weakness:
            damage *= 2
        elif action.source.cardType in action.target.resistance:
            if damage >= 30:
                damage -= 30
            else:
                damage = 0

        player = current_player(state)
        player.reward.apply_damage_dealt_reward(damage)

        # Check if the Pokemon will be knocked out
        is_knocked_out = action.target.hp <= damage

        if not is_knocked_out:
            # Pokemon survives - just deal damage
            action.target.hp -= damage
        else:
            # Pokemon is knocked out - apply extra prize card effect
            opponent = opponent_player(state)
            discard_pokemon(opponent, action.target)
            opponent.hasPokemonDead = True

            # Calculate total prize cards: normal prize + 1 extra for Amp You Very Much
            base_prize = action.target.prize
            total_prize = base_prize + 1  # Extra prize card from Amp You Very Much

            # Choose prize cards (normal + extra)
            tips = f"Congratulations! You may choose {min(len(player.prize), total_prize)} prize card(s) and put them into your hand. (Including 1 extra prize card from Amp You Very Much)"
            player.reward.apply_prize_card_reward(min(len(player.prize), total_prize))

            actions = choose_card_actions(
                player.id,
                player.id,
                min(len(player.prize), total_prize),
                min(len(player.prize), total_prize),
                player.prize,
                hidden=True,
                tips=tips,
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            move_cards(
                chosen_card,
                (player.id, CardPosition.PRIZE),
                (player.id, CardPosition.HAND),
                state,
            )

            # Check if game ends
            if len(player.prize) == 0:
                raise GameTermination

            # Choose a new pokemon to active
            if len(opponent.bench) == 0:
                raise GameTermination

            # Change turn to opponent for active Pokemon selection
            state.turn = opponent.id
            tips = "Your active Pokemon is knocked out. You have to choose 1 of your benched Pokemon and switch it to your active spot."
            actions = choose_card_actions(opponent.id, opponent.id, 1, 1, opponent.bench, tips=tips)
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            chosen_card = chosen_card[0]
            from ptcg.utils.utils import move_pokemon

            move_pokemon(opponent, chosen_card)

            # Restore turn
            state.turn = player.id

        # End turn
        from ptcg.utils.utils import next_turn

        next_turn(state)
