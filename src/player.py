import random
from pydantic import BaseModel
from card import Card
from typing import List
from action import Action, ActionType
from character import Character


class Player(BaseModel):
    id: int
    name: str
    hand: List[Card]
    coins: int
    nb_remaining_cards: int
    can_coup: bool
    must_coup: bool
    is_alive: bool

    def is_bluffing(self, action: Action):
        match action.action_type:
            case ActionType.DUKE:
                for card in self.hand:
                    if card.character == Character.DUKE and not card.is_revealed:
                        return False
                return True, card
            # TODO remaining cases
            case _:
                return False, None

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

    def lose_one_influence(self):
        # If first card is revealed, reveal second card
        if self.hand[0].is_revealed:
            self.hand[1].is_revealed = True
            revealed_card = self.hand[1]
        # If second card is revealed, reveal first card
        elif self.hand[1].is_revealed:
            self.hand[0].is_revealed = True
            revealed_card = self.hand[0]
        # If no card is revealed, randomly reveal one
        else:
            if random.random() < 0.5:
                self.hand[0].is_revealed = True
                revealed_card = self.hand[0]
            else:
                self.hand[1].is_revealed = True
                revealed_card = self.hand[1]

        # Check if both cards are revealed to determine if player is dead
        if self.hand[0].is_revealed and self.hand[1].is_revealed:
            self.is_alive = False
            self.coins = 0

        return revealed_card

    def gain_coins(self, amount: int):
        self.coins += amount
        self.update_coup_status()

    def lose_coins(self, amount: int):
        self.coins -= amount
        self.update_coup_status()

    def lose_card(self, card: Card):
        self.hand.pop(self.hand.index(card))

    def action_revenue(self):
        self.gain_coins(1)
        self.update_coup_status()

    def action_foreign_aid(self):
        self.gain_coins(2)
        self.update_coup_status()

    def action_coup(self, target_player):
        if self.coins >= 7:
            self.lose_coins(7)
            self.update_coup_status()
            target_player.lose_one_influence()
        self.update_coup_status()

    ## character actions

    # basic actions
    def action_duke(self):
        self.gain_coins(3)
        self.update_coup_status()
        print(
            f"Player {self.name} gained 3 coins with duke and has now {self.coins} coins"
        )

    def action_assassin(self):
        pass

    def action_ambassador(self):
        pass

    def action_captain(self):
        pass

    def action_contessa(self):
        pass

    # counters
    def action_duke_counter(self):
        pass

    def action_assassin_counter(self):
        pass

    def action_ambassador_counter(self):
        pass

    def action_captain_counter(self):
        pass

    def action_contessa_counter(self):
        pass
