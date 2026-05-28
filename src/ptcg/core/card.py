import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ptcg.core.ability import Ability
from ptcg.core.attack import Attack
from ptcg.core.enums import *


def _build_ability_info(ability) -> Dict[str, Any]:
    info: Dict[str, Any] = {"name": ability.name}
    if hasattr(ability, "text") and ability.text:
        info["text"] = ability.text
    return info


def _build_attack_info(attack) -> Dict[str, Any]:
    info: Dict[str, Any] = {"name": attack.name, "cost": [e.name for e in attack.cost]}
    if hasattr(attack, "damage"):
        info["damage"] = attack.damage
    if hasattr(attack, "text") and attack.text:
        info["text"] = attack.text
    return info


class Card(ABC):
    id: str
    name: str
    set_name: str
    number: str
    superType: SuperType
    cardType: CardType
    cardPosition: CardPosition
    index: int  # 0 for unkwown, valid index start from 1

    @abstractmethod
    def get_actions(self, state):
        pass

    def to_dict(self):
        result = {}
        result["name"] = self.name
        result["set_name"] = self.set_name
        result["number"] = self.number
        return result

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cardType": self.cardType.name
            if hasattr(self.cardType, "name")
            else str(self.cardType),
            "superType": self.superType.name
            if hasattr(self.superType, "name")
            else str(self.superType),
        }


def get_card_info(card: Card) -> str:
    return json.dumps(card.get_info(), ensure_ascii=False, indent=2)


class PokemonCard(Card):
    hp: int
    cardTag: CardTag
    pokemonType: PokemonType
    pokemonRule: PokemonRule
    stage: Stage
    retreat: List[CardType]
    weakness: List[CardType]
    resistance: List[CardType]
    prize: int

    position: PokemonPosition

    energy: List[CardType]
    attachment: List[Card]

    evolveFrom: List[str]
    evolved: List[Card]

    attacks: List[Attack]
    ability: List[Ability]

    firstTurnPlayed: bool

    def __init__(self) -> None:
        super().__init__()
        self.superType = SuperType.POKEMON
        self.firstTurnPlayed = True

    def to_dict(self):
        result = super().to_dict()
        result["hp"] = str(self.hp)
        result["tool"] = []
        result["energy"] = []
        result["evolved"] = []
        result["attachment"] = []

        result["attachment"].append(self.name)
        for card in self.attachment:
            if isinstance(card, EnergyCard):
                result["energy"].append(card.provides[0].name.lower())
            if isinstance(card, ToolCard):
                result["tool"].append(card.name)
            result["attachment"].append(card.name)

        if hasattr(self, "evolved"):
            for card in self.evolved:
                result["evolved"].append(card.name)

        return result

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()
        info["pokemonType"] = self.pokemonType.name
        info["hp"] = self.hp
        info["prize"] = self.prize
        info["stage"] = self.stage.name
        info["retreatCost"] = [e.name for e in self.retreat]

        if hasattr(self, "evolveFrom") and self.evolveFrom:
            info["evolveFrom"] = self.evolveFrom
        if hasattr(self, "weakness") and self.weakness:
            info["weakness"] = [w.name for w in self.weakness]
        if hasattr(self, "resistance") and self.resistance:
            info["resistance"] = [r.name for r in self.resistance]
        if hasattr(self, "ability") and self.ability:
            info["abilities"] = [_build_ability_info(a) for a in self.ability]
        if self.attacks:
            info["attacks"] = [_build_attack_info(a) for a in self.attacks]

        return info


class EnergyCard(Card):
    provides: List[CardType]
    energyType: EnergyType

    def __init__(self) -> None:
        super().__init__()
        self.superType = SuperType.ENERGY

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()
        info["energyType"] = self.energyType.name
        info["provides"] = [e.name for e in self.provides]
        if hasattr(self, "text") and self.text:
            info["effect"] = self.text
        return info


class TrainerCard(Card):
    trainerType: TrainerType

    def __init__(self) -> None:
        super().__init__()
        self.superType = SuperType.TRAINER

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()
        info["trainerType"] = self.trainerType.name
        if hasattr(self, "text") and self.text:
            info["effect"] = self.text
        return info


class ItemCard(TrainerCard):
    def __init__(self) -> None:
        super().__init__()
        self.superType = SuperType.TRAINER
        self.trainerType = TrainerType.ITEM


class SupporterCard(TrainerCard):
    def __init__(self) -> None:
        super().__init__()
        self.superType = SuperType.TRAINER
        self.trainerType = TrainerType.SUPPORTER


class StadiumCard(TrainerCard):
    playedFrom: Optional[PlayerId]

    def __init__(self) -> None:
        super().__init__()
        self.superType = SuperType.TRAINER
        self.trainerType = TrainerType.STADIUM


class ToolCard(TrainerCard):
    attacks: List[Attack]
    ability: List[Ability]
    hasAttached: bool

    def __init__(self) -> None:
        super().__init__()
        self.superType = SuperType.TRAINER
        self.trainerType = TrainerType.TOOL

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()
        if hasattr(self, "ability") and self.ability:
            info["abilities"] = [_build_ability_info(a) for a in self.ability]
        if hasattr(self, "attacks") and self.attacks:
            info["attacks"] = [_build_attack_info(a) for a in self.attacks]
        return info
