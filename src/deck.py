import random
from card import Card
from character import Character

class Deck():
    deck: list[Card]
    nb_instances_of_each_character: int

    def __init__(self, nb_instances_of_each_character: int=3):
        self.deck = []
        for _ in range(nb_instances_of_each_character):
            self.deck.extend([
                Card(character=Character.DUKE, is_revealed=False),
                Card(character=Character.ASSASSIN, is_revealed=False),
                Card(character=Character.AMBASSADOR, is_revealed=False),
                Card(character=Character.CAPTAIN, is_revealed=False),
                Card(character=Character.CONTESSA, is_revealed=False)
            ])
        self.nb_instances_of_each_character = nb_instances_of_each_character
        
    def shuffle(self):
        random.shuffle(self.deck)

    def draw(self):
        return self.deck.pop()