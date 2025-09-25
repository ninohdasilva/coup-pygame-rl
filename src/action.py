from enum import Enum
from pydantic import BaseModel


class ActionType(Enum):
    DO_NOTHING = 0
    REVENUE = 1
    FOREIGN_AID = 2
    DUKE = 3
    CHALLENGE = 4
    AMBASSADOR = 5
    ASSASSIN_TARGET_PLAYER_0 = 6
    ASSASSIN_TARGET_PLAYER_1 = 7
    ASSASSIN_TARGET_PLAYER_2 = 8
    ASSASSIN_TARGET_PLAYER_3 = 9
    COUP_TARGET_PLAYER_0 = 10
    COUP_TARGET_PLAYER_1 = 11
    COUP_TARGET_PLAYER_2 = 12
    COUP_TARGET_PLAYER_3 = 13
    CAPTAIN_TARGET_PLAYER_0 = 14
    CAPTAIN_TARGET_PLAYER_1 = 15
    CAPTAIN_TARGET_PLAYER_2 = 16
    CAPTAIN_TARGET_PLAYER_3 = 17
    COUNTER_FOREIGN_AID_WITH_DUKE = 18
    COUNTER_ASSASSIN_WITH_CONTESSA = 19
    COUNTER_CAPTAIN_WITH_CAPTAIN = 20
    COUNTER_CAPTAIN_WITH_AMBASSADOR = 21
    REVEAL_CARD_1 = 22
    REVEAL_CARD_2 = 23
    DISCARD_CAPTAIN = 24
    DISCARD_AMBASSADOR = 25
    DISCARD_ASSASSIN = 26
    DISCARD_DUKE = 27
    DISCARD_CONTESSA = 28


class Action(BaseModel):
    action_type: ActionType
    origin_player_id: int
    target_player_id: int
    can_be_countered: bool
    can_be_challenged: bool

    def __str__(self):
        return f"Action(action_type={self.action_type}, origin_player_id={self.origin_player_id}, target_player_id={self.target_player_id}, card_to_reveal={self.card_to_reveal}, can_be_countered={self.can_be_countered}, can_be_challenged={self.can_be_challenged})"
