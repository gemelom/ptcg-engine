from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import *
from ptcg.utils.utils import *


class OBF080Cleffa(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "OBF"
        self.number = "080"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Cleffa"
        self.hp = 30
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC
        self.retreat = []
        self.weakness = [CardType.METAL]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Grasping Draw",
                    "damage": 0,
                    "cost": [],
                    "text": "Draw cards until you have 7 cards in your hand.",
                }
            )
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
            player = current_player(state)

            if len(player.hand) < 7:
                draw_cards = player.left[: 7 - len(player.hand)]
                move_cards(
                    draw_cards,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )

            auto_end_turn(state)

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")
