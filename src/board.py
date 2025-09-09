import random
from player import Player
from deck import Deck

class Board:
    nb_players: int
    players: list[Player]
    alive_players: list[Player]
    next_player: Player
    deck: Deck
    game_has_started: bool
    game_has_ended: bool

    def __init__(self, nb_players: int=4):
        self.nb_players = nb_players
        self.players = []
        self.next_player = None
        self.game_has_started = False
        self.game_has_ended = True

    def start(self):
        self.game_has_started = True
        self.game_has_ended = False
        self.deck = Deck()
        self.deck.shuffle()
        # Clear existing players
        self.players = []
        # Create new players
        for i in range(self.nb_players):
            player = Player(id=i, name=f"Player {i}", hand=[self.deck.draw() for _ in range(2)], coins=2, can_coup=False, must_coup=False, is_alive=True, nb_remaining_cards=2)
            self.players.append(player)
        self.alive_players = self.players.copy()
        self.next_player = random.choice(self.alive_players)

    def player_try_action(self, player: Player, last_actions: list[str]):
        # Check if player is actually alive (has at least one unrevealed card)
        if all(card.is_revealed for card in player.hand):
            player.is_alive = False
            # Immediately check if game has ended
            self.check_if_game_has_ended()
            return last_actions
            
        if player.can_coup or player.must_coup:
            # Find valid targets (alive players with unrevealed cards)
            possible_targets = [p for p in self.players 
                              if p.id != player.id 
                              and p.is_alive 
                              and any(not card.is_revealed for card in p.hand)]
            
            if possible_targets:  # Only coup if there are valid targets
                target_player = random.choice(possible_targets)
                player.action_coup(target_player)
                last_actions.append(f"{player.name} launched a Coup on {target_player.name}")
                
                # Immediately check if target died and if game has ended
                if all(card.is_revealed for card in target_player.hand):
                    target_player.is_alive = False
                    self.check_if_game_has_ended()
            else:  # If no valid targets, just take revenue
                player.action_revenue()
                last_actions.append(f"{player.name} collected 1 coin with revenue")
        else:
            player.action_revenue()
            last_actions.append(f"{player.name} collected 1 coin with revenue")
        
        if len(last_actions) > 3:
            last_actions.pop(0)
        return last_actions

    def update_state(self):
        pass

    def check_if_game_has_ended(self):
        # Get players who are still in the game (have at least one unrevealed card)
        self.alive_players = [player for player in self.players 
                            if any(not card.is_revealed for card in player.hand)]
        
        # Update alive status
        for player in self.players:
            player.is_alive = any(not card.is_revealed for card in player.hand)
        
        # Game ends when only one player has unrevealed cards
        if len(self.alive_players) == 1:
            self.game_has_ended = True
            self.game_has_started = False
            return True
            
        return False

    def next_move(self, last_actions: list[str]):
        # First check if current player is dead
        if all(card.is_revealed for card in self.next_player.hand):
            self.next_player.is_alive = False
        
        # Update alive players list and check game end
        self.alive_players = [player for player in self.players 
                            if any(not card.is_revealed for card in player.hand)]
        
        if self.check_if_game_has_ended():
            return []
        
        # If current player is dead, find next alive player without taking action
        if not self.next_player.is_alive:
            current_position = self.players.index(self.next_player)
            for i in range(1, len(self.players)):
                next_position = (current_position + i) % len(self.players)
                if any(not card.is_revealed for card in self.players[next_position].hand):
                    self.next_player = self.players[next_position]
                    break
            return last_actions
        
        # Current player is alive, let them take action
        last_actions = self.player_try_action(self.next_player, last_actions)
        
        # Find next alive player
        current_position = self.players.index(self.next_player)
        for i in range(1, len(self.players)):
            next_position = (current_position + i) % len(self.players)
            if any(not card.is_revealed for card in self.players[next_position].hand):
                self.next_player = self.players[next_position]
                break
        
        return last_actions