from typing import List

from ptcg.core.enums import (
    CardType,
)


class Attack:
    name: str
    damage: int
    cost: List[CardType]
    text: str

    def __init__(self, attributes):
        self.name = attributes.get("name")
        self.damage = attributes.get("damage")
        self.cost = attributes.get("cost")
        self.text = attributes.get("text")
