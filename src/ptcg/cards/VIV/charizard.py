from ptcg.core.ability import ActiveAbility
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import *


class VIV029Charizard(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "VIV"
        self.number = "025"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "Charizard"
        self.hp = 170
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.FIRE
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.WATER]
        self.resistance = []
        self.prize = 1

        self.energy = []
        self.attachment = []

        self.evolveFrom = ["Charmeleon", "Charmander"]
        self.evolved = []

        self.attacks = [
            Attack(
                {
                    "name": "Royal Blaze",
                    "damage": 100,
                    "cost": [CardType.FIRE, CardType.FIRE],
                    "text": "This attack does 50 more damage for each Leon card in your discard pile.",
                }
            )
        ]

        self.ability = [
            ActiveAbility(
                {
                    "name": "Battle Sense",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": True,
                    "text": "Once during your turn, you may look at the top 3 cards of your "
                    "deck and put 1 of them into your hand. Discard the other cards.",
                }
            )
        ]

    def get_actions(self, state):
        return []
