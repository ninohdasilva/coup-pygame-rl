from calendar import c
import random
import numpy as np
from action import Action, ActionType
from card import Card
from character import Character
from player import Player
from deck import Deck
from agent import CoupAgent

class Board:
    nb_players: int
    players: list[Player]
    agents: list[CoupAgent]
    alive_players: list[Player]
    next_player: Player
    deck: Deck
    game_has_started: bool
    game_has_ended: bool

    def __init__(self, nb_players: int=4):
        self.nb_players = nb_players
        self.players = []
        self.agents = []
        self.next_player = None
        self.game_has_started = False
        self.game_has_ended = True
    
    def get_player_by_id(self, id: int):
        return self.players[id]

    def player_return_card_to_deck(self, card: Card, player: Player):
        self.deck.add_card(card)
        player.lose_card(card)
    
    def player_draw_single_card(self, player: Player):
        player.hand.append(self.deck.draw())

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
        self.agents = [CoupAgent(i) for i in range(self.nb_players)]
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

    def update_states(self, last_actions: list[Action]):
        """Convert the game state into a numerical representation"""
        for agent in self.agents:
            state = []
            player = self.players[agent.player_id]
            
            # Encode own cards (2 cards x 5 characters + 2 revealed flags)
            for card in player.hand:
                # One-hot encoding for character type
                for char in Character:
                    state.append(1 if card.character == char else 0)
            # Add revealed status for both cards
            state.append(1 if player.hand[0].is_revealed else 0)
            state.append(1 if player.hand[1].is_revealed else 0)
                
            # Encode own coins
            state.append(player.coins)
            
            # Encode other players' information
            for other_player in self.players:
                if other_player != player:
                    # Encode their cards (only if revealed)
                    for card in other_player.hand:
                        for char in Character:
                            # Only see character if card is revealed
                            state.append(1 if (card.is_revealed and card.character == char) else 0)
                    # Add revealed status for both cards
                    state.append(1 if other_player.hand[0].is_revealed else 0)
                    state.append(1 if other_player.hand[1].is_revealed else 0)
                    # Encode their coins
                    state.append(other_player.coins)
            
            # Encode last actions
            for action in last_actions:
                pass
            
            agent.state = np.array(state, dtype=int)

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

    def execute_action(self, player: Player, action: Action, last_actions: list[str]):
        if not action.can_be_challenged and not action.can_be_countered:
            # Revenue
            if action.action_type == ActionType.REVENUE:
                player.action_revenue()
                last_actions.append(f"{player.name} collected 1 coin with revenue")
            # Coup
            elif action.action_type == ActionType.COUP:
                target_player = self.players[action.target_player_id]
                player.action_coup(target_player)
                last_actions.append(f"{player.name} launched a Coup on {target_player.name}")
        else:
            if action.can_be_challenged:
                challenges = [agent.get_desired_challenge(player.id, self) for agent in self.agents if agent.player_id != player.id]
                challenges = [action for action in challenges if action.action_type == ActionType.CHALLENGE]
                if challenges:
                    selected_challenge = random.choice(challenges)
                    is_bluffing, card = player.is_bluffing(action)
                    if is_bluffing:
                        player.lose_one_influence()
                        last_actions.append(f"{player.name} was bluffing and lost an influence")
                    else:
                        selected_challenged_player = self.get_player_by_id(selected_challenge.origin_player_id)
                        selected_challenged_player.lose_one_influence()
                        last_actions.append(f"{selected_challenged_player.name} lost his challenge and lost an influence")
                        
                        if action.action_type == ActionType.DUKE: # TODO remaining cases
                                self.player_return_card_to_deck(card, player)
                                self.player_draw_single_card(player)
                                player.action_duke()
                                last_actions.append(f"{player.name} gained 3 coins with duke")
        #                     
        #             
        #     
        #             
        # if action.can_be_countered:
        #     if action.action_type == ActionType.FOREIGN_AID:
        #         counters = [get_desired_action(self) for agent in self.agents if agent.player_id != player.id]
        #         counters = [action for action in counters if action.action_type == ActionType.COUNTER_FOREIGN_AID_WITH_DUKE]
        #         if counters:
        #             TODO (recursive method ?)
        #     else:
        #         player.action_foreign_aid()
        #         last_actions.append(f"{player.name} collected 2 coins with foreign aid")
        # if action.can_be_countered:
        #     if action.action_type == ActionType.DUKE:
        #         counters = [get_desired_action(self) for agent in self.agents if agent.player_id != player.id]
        #         counters = [action for action in counters if action.action_type == ActionType.COUNTER_FOREIGN_AID_WITH_DUKE]
        #         if counters:
        #             TODO (recursive method ?)
    
        #         else:
        #             player.action_foreign_aid()
        #             last_actions.append(f"{player.name} collected 2 coins with foreign aid")
    
    def agents_next_move(self, last_actions: list[str]):
        # Get current player and their agent
        current_player = self.next_player
        current_agent = self.agents[current_player.id]
        
        # Get state and desired action from agent
        desired_action = current_agent.get_desired_action(self)

        # Execute action and update states
        last_actions = self.execute_action(current_player, desired_action, last_actions)
        self.update_states(last_actions)

        return last_actions