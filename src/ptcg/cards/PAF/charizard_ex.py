from ptcg.core.ability import InstantAbility
from ptcg.core.action import (
    AttachEnergyAction,
    AttackAction,
    EvolvePokemonAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardType,
    EnergyType,
    PokemonRule,
    PokemonType,
    Stage,
    SuperType,
)
from ptcg.core.reducer import *
from ptcg.utils.utils import check_energy, current_all_pokemon, opponent_active, shuffle_cards


class PAF054CharizardEX(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Charizard ex"
        self.set_name = "PAF"
        self.number = "054"
        self.id = f"{self.set_name}-{self.number}"
        self.hp = 330
        self.pokemonType = PokemonType.EX
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.DARK
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.GRASS]
        self.resistance = []
        self.prize = 2

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Charmeleon", "Charmander"]
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Burning Darkness",
                    "damage": 180,
                    "cost": [CardType.FIRE, CardType.FIRE],
                    "text": "This attack does 30 more damage for each Prize card your opponent has taken.",
                }
            )
        ]

        self.ability = [
            InstantAbility(
                {
                    "name": "Infernal Reign",
                    "abilityType": AbilityType.INSTANT_ABILITY,
                    "onceUsedPerTurn": False,
                    "text": "When you play this Pokémon from your hand to evolve 1 of your Pokémon during your turn, "
                    "you may search your deck for up to 3 Basic Fire Energy cards and attach them to your Pokémon in any way you like. "
                    "Then, shuffle your deck.",
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
        if isinstance(action, EvolvePokemonAction):
            player = current_player(state)
            cards = [
                card
                for card in player.left
                if card.superType == SuperType.ENERGY
                and card.energyType == EnergyType.BASIC
                and CardType.FIRE in card.provides
            ]

            tips = "You used the ability Infernal Reign. You can choose up to 3 Basic Fire Energy cards from your deck and attach them to your Pokemon in any way you like."
            actions = choose_card_actions(
                player.id, player.id, 0, min(len(cards), 3), cards, tips=tips, source=self
            )

            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.left for card in chosen_card):
                # temporarily move chosen energies to hand
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

            for energy_card in chosen_card:
                tips = f"Choose 1 of your Pokemon in play to attach the {energy_card.name}."
                target_actions = choose_card_actions(
                    player.id, player.id, 1, 1, current_all_pokemon(state), tips=tips, source=self
                )
                target = yield from reduce_choose_card_actions(target_actions, state)
                reduce_attach_energy_action(
                    AttachEnergyAction(player.id, energy_card, target[0]), state
                )

            shuffle_cards(player.left)

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            # Infernal Reign
            reduce_evolve_pokemon_action(action, state)
            yield from self.use_ability(action, state)

        elif isinstance(action, AttackAction):
            # Burning Darkness
            opponent = opponent_player(state)
            action.attack.damage = 180 + 30 * (6 - len(opponent.prize))
            yield from reduce_attack_action(action, state)
