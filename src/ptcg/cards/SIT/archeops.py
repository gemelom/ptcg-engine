from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction,
    EvolvePokemonAction,
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
    EnergyType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
    SuperType,
)
from ptcg.core.reducer import (
    reduce_attack_action,
    reduce_choose_card_actions,
    reduce_evolve_pokemon_action,
    reduce_play_pokemon_action,
)
from ptcg.utils.utils import (
    check_energy,
    current_all_pokemon,
    current_player,
    move_cards,
    opponent_active,
    shuffle_cards,
)


class SIT147Archeops(PokemonCard):
    def __init__(self):
        super().__init__()
        self.set_name = "SIT"
        self.number = "147"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Archeops"
        self.hp = 150
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Archen"]
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Speed Wing",
                    "damage": 120,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS],
                    "text": "",
                }
            )
        ]

        self.abilityUsed = False
        self.ability = [
            ActiveAbility(
                {
                    "name": "Primal Turbo",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may search your deck for up to 2 Special Energy cards and attach them to 1 of your Pokemon in any way you like. Then, shuffle your deck.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)
        player = current_player(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        special_energy_cards = [
            card
            for card in player.left
            if card.superType == SuperType.ENERGY
            and hasattr(card, "energyType")
            and card.energyType == EnergyType.SPECIAL
        ]
        if (
            not self.abilityUsed
            and not player.onceUsedTurn.get(self.ability[0].name, False)
            and len(special_energy_cards) > 0
        ):
            actions.append(UseAbilityAction(state.turn, self, self.ability[0]))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)

            special_energy_cards = [
                card
                for card in player.left
                if card.superType == SuperType.ENERGY
                and hasattr(card, "energyType")
                and card.energyType == EnergyType.SPECIAL
            ]

            max_energy = min(len(special_energy_cards), 2)
            tips = "You used the ability Primal Turbo. Choose up to 2 Special Energy cards from your deck."
            actions = choose_card_actions(
                player.id, player.id, 0, max_energy, special_energy_cards, tips=tips, source=self
            )

            chosen_energy_cards = yield from reduce_choose_card_actions(actions, state)

            if chosen_energy_cards:
                all_pokemon = current_all_pokemon(state)
                tips = f"Choose 1 of your Pokemon to attach {len(chosen_energy_cards)} Special Energy card(s) to."
                pokemon_actions = choose_card_actions(
                    player.id, player.id, 1, 1, all_pokemon, tips=tips, source=self
                )

                target_pokemon = yield from reduce_choose_card_actions(pokemon_actions, state)
                target = target_pokemon[0]

                for energy_card in chosen_energy_cards:
                    target.energy.extend(energy_card.provides)
                    target.attachment.append(energy_card)
                    if target.cardPosition == CardPosition.ACTIVE:
                        move_cards(
                            energy_card,
                            (player.id, CardPosition.LEFT),
                            (player.id, CardPosition.ACTIVE_ATTACHMENT, target.index),
                            state,
                        )
                    else:
                        move_cards(
                            energy_card,
                            (player.id, CardPosition.LEFT),
                            (player.id, CardPosition.BENCH_ATTACHMENT, target.index),
                            state,
                        )
                    player.reward.apply_energy_attached_reward(1)

            shuffle_cards(player.left)
            self.abilityUsed = True
            player.onceUsedTurn[action.ability.name] = True

    def reset_turn_stats(self):
        self.abilityUsed = False
