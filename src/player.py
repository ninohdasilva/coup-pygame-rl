from pydantic import BaseModel
from card import Card
from typing import List
from action import Action, ActionType
from character import Character


class Player(BaseModel):
    id: int
    agent_id: int = None
    name: str
    hand: List[Card]
    coins: int
    nb_remaining_cards: int
    can_coup: bool
    must_coup: bool
    is_alive: bool

    def is_bluffing(self, action: Action):
        match action.action_type:
            case ActionType.DUKE | ActionType.COUNTER_FOREIGN_AID_WITH_DUKE:
                for card in self.hand:
                    if card.character == Character.DUKE and not card.is_revealed:
                        return False, card
                return True, None
            case ActionType.ASSASSIN:
                for card in self.hand:
                    if card.character == Character.ASSASSIN and not card.is_revealed:
                        return False, card
                return True, None
            case ActionType.AMBASSADOR | ActionType.COUNTER_CAPTAIN_WITH_AMBASSADOR:
                for card in self.hand:
                    if card.character == Character.AMBASSADOR and not card.is_revealed:
                        return False, card
                return True, None
            case ActionType.CAPTAIN | ActionType.COUNTER_CAPTAIN_WITH_CAPTAIN:
                for card in self.hand:
                    if card.character == Character.CAPTAIN and not card.is_revealed:
                        return False, card
                return True, None
            case ActionType.COUNTER_ASSASSIN_WITH_CONTESSA:
                for card in self.hand:
                    if card.character == Character.CONTESSA and not card.is_revealed:
                        return False, card
                return True, None
            case (
                ActionType.CHALLENGE
                | ActionType.REVENUE
                | ActionType.FOREIGN_AID
                | ActionType.COUP
                | ActionType.DO_NOTHING
            ):
                print(f"Action {action.action_type} is not a bluff")
                return False, None
            case _:
                return ValueError(f"Unknown action type: {action.action_type}")

    def update_can_coup(self):
        if self.coins >= 7:
            self.can_coup = True
        else:
            self.can_coup = False

    def update_must_coup(self):
        if self.coins >= 10:
            self.must_coup = True
        else:
            self.must_coup = False

    def update_coup_status(self):
        self.update_can_coup()
        self.update_must_coup()

    def gain_coins(self, amount: int):
        self.coins += amount
        self.update_coup_status()

    def lose_coins(self, amount: int):
        print(f"Player {self.name} Initial coins: {self.coins}")
        self.coins -= amount
        print(f"Player {self.name} Coins after losing {amount}: {self.coins}")
        self.update_coup_status()

    def lose_card(self, card: Card):
        self.hand.pop(self.hand.index(card))

    def get_revenue(self):
        self.gain_coins(1)
        self.update_coup_status()

    def get_foreign_aid(self):
        self.gain_coins(2)
        self.update_coup_status()

    def pay_coup(self, target_player):
        # Lost influence is handled by target player's agent
        if self.coins >= 7:
            self.lose_coins(7)
            self.update_coup_status()
        self.update_coup_status()

    ## character actions (only handles impact on self)

    def pay_assassin(self):
        # Eventual lost influence is handled by target player's agent
        self.lose_coins(3)
        self.update_coup_status()
        pass
