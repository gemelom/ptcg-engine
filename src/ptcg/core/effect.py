from ptcg.core.enums import SpecialCondition


class Effect:
    dc: int
    specialCondition: SpecialCondition

    def __init__(self, dc, specialCondition=SpecialCondition.NONE):
        self.dc = dc
        self.specialCondition = specialCondition
