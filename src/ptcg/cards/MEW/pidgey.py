from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonRule, PokemonType, Stage, SuperType
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class MEW016Pidgey(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "MEW"
        self.number = "016"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Pidgey"
        self.hp = 50
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Call for Family",
                    "damage": 0,
                    "cost": [CardType.COLORLESS],
                    "text": "Search your deck for up to 2 Basic Pokémon and put them onto your Bench. Then, shuffle your deck.",
                }
            ),
            Attack(
                {
                    "name": "Tackle",
                    "damage": 20,
                    "cost": [CardType.COLORLESS, CardType.COLORLESS],
                    "text": "",
                }
            ),
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)
        player = current_player(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if (
                    check_energy(attack.cost, self.energy)
                    and player.benchSize - len(player.bench) >= 1
                ):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            if action.attack == self.attacks[0]:
                player = current_player(state)
                cards = [
                    card
                    for card in player.left
                    if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
                ]
                bench_left = player.benchSize - len(player.bench)

                tips = f"You used the attack Call for Family. You can choose up to {min(len(cards), bench_left, 2)} Pokemon(s) from your deck, and put them onto your bench."
                actions = choose_card_actions(
                    player.id,
                    player.id,
                    0,
                    min(len(cards), bench_left, 2),
                    cards,
                    tips=tips,
                    source=self,
                )

                chosen_card = yield from reduce_choose_card_actions(actions, state)
                if all(card in player.left for card in chosen_card):
                    move_cards(
                        chosen_card,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.BENCH),
                        state,
                    )
                    for card in chosen_card:
                        card.position = PokemonPosition.BENCH
                else:
                    print(chosen_card)
                    print(player.left)
                    raise ValueError(f"Invalid action: {action}")

                shuffle_cards(player.left)
                auto_end_turn(state)

            elif action.attack == self.attacks[1]:
                yield from reduce_attack_action(action, state)
