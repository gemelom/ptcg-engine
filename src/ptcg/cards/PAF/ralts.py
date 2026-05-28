from ptcg.core.action import AttackAction, PlayPokemonAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_play_pokemon_action
from ptcg.utils.utils import check_energy, opponent_active


class PAF027Ralts(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Ralts"
        self.set_name = "PAF"
        self.number = "027"
        self.id = f"{self.set_name}-{self.number}"

        self.hp = 70
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
                    "name": "Psyshot",
                    "damage": 30,
                    "cost": [CardType.PSYCHIC, CardType.COLORLESS],
                    "text": "",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
