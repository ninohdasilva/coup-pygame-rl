from enum import Enum
from pydantic import BaseModel


class ActionStatus(Enum):
    SUCCESS = 0
    FAILURE = 1
    CHALLENGED = 2
    CHALLENGED_SUCCESS = 3
    CHALLENGED_FAILURE = 4


class ActionType(Enum):
    LOSE_ONE_INFLUENCE = -1
    DO_NOTHING = 0
    REVENUE = 1
    COUP = 2
    DUKE = 3
    ASSASSIN = 4
    AMBASSADOR = 4
    CAPTAIN = 5
    CONTESSA = 6
    COUNTER_FOREIGN_AID_WITH_DUKE = 7
    COUNTER_ASSASSIN_WITH_CONTESSA = 8
    COUNTER_CAPTAIN_WITH_CAPTAIN = 9
    COUNTER_CAPTAIN_WITH_AMBASSADOR = 10
    CHALLENGE = 11


class Action(BaseModel):
    action_type: ActionType
    origin_player_id: int
    target_player_id: int
    card_to_reveal: int
    can_be_countered: bool
    can_be_challenged: bool

    def __str__(self):
        return f"Action(action_type={self.action_type}, origin_player_id={self.origin_player_id}, target_player_id={self.target_player_id}, card_to_reveal={self.card_to_reveal}, can_be_countered={self.can_be_countered}, can_be_challenged={self.can_be_challenged})"
