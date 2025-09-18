from enum import Enum
from pydantic import BaseModel


class ActionType(Enum):
    DO_NOTHING = 0
    REVENUE = 1
    FOREIGN_AID = 2
    DUKE = 3
    CHALLENGE = 4
    AMBASSADOR = 5
    ASSASSIN = 6
    COUP = 7
    CAPTAIN = 8
    CONTESSA = 9
    COUNTER_FOREIGN_AID_WITH_DUKE = 10
    COUNTER_ASSASSIN_WITH_CONTESSA = 11
    COUNTER_CAPTAIN_WITH_CAPTAIN = 12
    COUNTER_CAPTAIN_WITH_AMBASSADOR = 13
    REVEAL_CARD_1 = 14
    REVEAL_CARD_2 = 15


class Action(BaseModel):
    action_type: ActionType
    origin_player_id: int
    target_player_id: int
    card_to_reveal: int
    can_be_countered: bool
    can_be_challenged: bool

    def __str__(self):
        return f"Action(action_type={self.action_type}, origin_player_id={self.origin_player_id}, target_player_id={self.target_player_id}, card_to_reveal={self.card_to_reveal}, can_be_countered={self.can_be_countered}, can_be_challenged={self.can_be_challenged})"
