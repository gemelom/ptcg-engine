from abc import ABC

from ptcg.core.enums import AbilityTrigger, AbilityType


class Ability(ABC):
    name: str
    abilityType: AbilityType
    onceUsedPerTurn: bool
    text: str

    def __init__(self, attributes):
        self.name = attributes.get("name")
        self.abilityType = attributes.get("abilityType")
        self.onceUsedPerTurn = attributes.get("onceUsedPerTurn")
        self.text = attributes.get("text")


class ActiveAbility(Ability):
    def __init__(self, attributes):
        super().__init__(attributes)


class PassiveAbility(Ability):
    abilityTrigger: AbilityTrigger
    suppresses_opponent_active_abilities: bool

    def __init__(self, attributes):
        super().__init__(attributes)
        self.abilityTrigger = attributes.get("abilityTrigger")
        self.suppresses_opponent_active_abilities = False


class InstantAbility(Ability):
    def __init__(self, attributes):
        super().__init__(attributes)
