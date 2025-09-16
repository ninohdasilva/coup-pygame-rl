from enum import Enum


class Character(Enum):
    DUKE = "DUKE"
    ASSASSIN = "ASSASSIN"
    AMBASSADOR = "AMBASSADOR"
    CAPTAIN = "CAPTAIN"
    CONTESSA = "CONTESSA"

    def to_int(self):
        match self:
            case Character.DUKE:
                return 1
            case Character.ASSASSIN:
                return 2
            case Character.AMBASSADOR:
                return 3
            case Character.CAPTAIN:
                return 4
            case Character.CONTESSA:
                return 5
