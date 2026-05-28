from enum import Enum


class CardTag(Enum):
    SP = "SP"
    EX = "EX"
    GX = "GX"
    LV_X = "LV_X"
    VSTAR = "VSTAR"
    ACE_SPEC = "ACE_SPEC"
    # POKEMON_SP = "SP"
    # POKEMON_EX = "EX"
    # POKEMON_GX = "GX"
    # POKEMON_LV_X = "LV_X"


class SuperType(Enum):
    NONE = 1
    POKEMON = 2
    TRAINER = 3
    ENERGY = 4


class EnergyType(Enum):
    BASIC = 1
    SPECIAL = 2


class TrainerType(Enum):
    ITEM = 1
    SUPPORTER = 2
    STADIUM = 3
    TOOL = 4


class PokemonType(Enum):
    NORMAL = 1
    EX = 2
    LEGEND = 3
    V = 4
    VSTAR = 5


class PokemonRule(Enum):
    NONE = 1
    TERA = 2
    ANCIENT = 3
    FUTURE = 4
    RADIANT = 5


class Stage(Enum):
    NONE = 1
    RESTORED = 2
    BASIC = 3
    STAGE_1 = 4
    STAGE_2 = 5


class CardType(Enum):
    ANY = 1
    NONE = 2
    COLORLESS = 3
    GRASS = 4
    FIGHTING = 5
    PSYCHIC = 6
    WATER = 7
    LIGHTNING = 8
    METAL = 9
    DARK = 10
    FIRE = 11
    DRAGON = 12
    FAIRY = 13


class SpecialCondition(Enum):
    NONE = 0
    PARALYZED = 1
    CONFUSED = 2
    ASLEEP = 3
    POISONED = 4
    BURNED = 5


class Coin(Enum):
    HEAD = 0
    TAIL = 1


class PlayerId(Enum):
    PLAYER1 = 1
    PLAYER2 = 2


class ActionType(Enum):
    ATTACK_ACTION = 1
    EFFECT_ACTION = 2
    USE_ABILITY_ACTION = 3
    USE_STADIUM_ACTION = 4
    RETREAT_ACTION = 5
    PLAY_POKEMON_ACTION = 6
    ATTACH_ENERGY_ACTION = 7
    USE_ITEM_ACTION = 8
    USE_SUPPORTER_ACTION = 9
    USE_TOOL_ACTION = 10
    PUT_STADIUM_ACTION = 11
    DISCARD_STADIUM_ACTION = 12
    PASS_TURN = 13
    EVOLVE_POKEMON_ACTION = 14  # Was merged with PLAY_POKEMON_ACTION (bug)

    # TODO: Extras
    CHOOSE_CARD_ACTION = 15


class AbilityType(Enum):
    ACTIVE_ABILITY = 1
    PASSIVE_ABILITY = 2
    INSTANT_ABILITY = 3


class EffectType(Enum):
    FIND_CARD = 1
    ONTO_BENCH = 2
    SHUFFLE_DECK = 3
    ATTACK_EFFECT = 4


class PokemonPosition(Enum):
    ACTIVE = 1
    BENCH = 2


class CardPosition(Enum):
    UNKNOWN = 0
    ACTIVE = 1
    BENCH = 2
    HAND = 3
    LEFT = 4
    DISCARD = 5
    LOSTZONE = 6
    PRIZE = 7
    STADIUM = 8
    ACTIVE_ATTACHMENT = 9
    BENCH_ATTACHMENT = 10

    def _i2n(self, opponent=False):
        num = 0
        if self.value == 1:
            num = 0
        elif self.value == 2:
            num = 1
        elif self.value == 3:
            num = 6
        elif self.value == 4:
            num = 26
        elif self.value == 5:
            num = 86
        elif self.value == 6:
            return 147
        elif self.value == 7:
            num = 147
        elif self.value == 8:
            return 160

        if opponent:
            num += 153
        return num


class AbilityTrigger(Enum):
    ATTACKING = 1
    ATTACKED = 2
    RETREAT = 3
    OTHER = 4
