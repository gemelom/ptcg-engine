from ptcg.core.action import *
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, PokemonType, Stage
from ptcg.core.reducer import *
from ptcg.utils.utils import check_energy, current_player, move_cards, opponent_active


class VIV028Charmeleon(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "VIV"
        self.number = "024"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Charmeleon"
        self.hp = 90
        self.pokemonType = PokemonType.NORMAL
        self.stage = Stage.STAGE_1
        self.cardType = CardType.FIRE
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.WATER]
        self.evolveFrom = ["Charmander"]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Charmander"]
        self.evolved = []

        self.attacks = [
            Attack({"name": "Slash", "damage": 20, "cost": [CardType.FIRE], "text": ""}),
            Attack(
                {
                    "name": "Raging Flames",
                    "damage": 60,
                    "cost": [CardType.FIRE, CardType.FIRE],
                    "text": "Discard the top 3 cards of your deck.",
                }
            ),
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    for target in targets:
                        actions.extend([AttackAction(state.turn, self, attack, target)])

        return actions

    def reduce_action(self, action, state):
        player = current_player(state)
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
            if action.attack == self.attacks[1]:  # Raging Flames: discard top 3 cards of deck
                top_cards = player.left[:3]
                if top_cards:
                    move_cards(
                        top_cards,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.DISCARD),
                        state,
                    )

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
