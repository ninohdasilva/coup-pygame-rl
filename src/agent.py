import torch
import random
import numpy as np
from collections import deque
from character import Character
from board import Board

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class CoupAgent:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.gamma = 0.9  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)
        
        # State size: 
        # - Own cards (2 cards x 5 possible characters + 2 revealed flags) = 12
        # - Other players (3 players x (2 cards x 5 characters + 2 revealed flags + coins)) = 3 * 13 = 39
        # - Own coins = 1
        # Total state size = 52
        # state_size = 52
        
        # Action size:
        # - Basic actions (revenue=0, coup=1) = 2
        # - Assassination targets (3 other players) = 3
        # - Card to reveal when losing life (2 cards) = 2
        # Total action size = 7
        # action_size = 7
        
        # hidden_size = 256
        # self.model = Linear_QNet(state_size, hidden_size, action_size)
        # self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self, board: Board) -> np.ndarray:
        """Convert the game state into a numerical representation"""
        state = []
        player = board.players[self.player_id]
        
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
        for other_player in board.players:
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
        
        return np.array(state, dtype=int)

    # def get_reward(self, board: Board, done: bool) -> float:
    #     """Calculate reward for the current state"""
    #     player = board.players[self.player_id]
        
    #     if not player.is_alive:
    #         return -10.0  # Large negative reward for dying
        
    #     if done and player.is_alive:
    #         return 20.0  # Large positive reward for winning
            
    #     # Small positive reward for staying alive and having more coins
    #     reward = 0.1 + (player.coins * 0.1)
        
    #     # Small negative reward for having revealed cards
    #     for card in player.hand:
    #         if card.is_revealed:
    #             reward -= 0.2
                
    #     return reward

    # def remember(self, state, action, reward, next_state, done):
    #     self.memory.append((state, action, reward, next_state, done))

    # def train_long_memory(self):
    #     if len(self.memory) == 0:
    #         return
            
    #     if len(self.memory) > BATCH_SIZE:
    #         mini_sample = random.sample(self.memory, BATCH_SIZE)
    #     else:
    #         mini_sample = self.memory

    #     # Convert the sampled experiences into numpy arrays
    #     states = np.array([np.array(state) for state, _, _, _, _ in mini_sample])
    #     actions = np.array([action for _, action, _, _, _ in mini_sample])
    #     rewards = np.array([reward for _, _, reward, _, _ in mini_sample])
    #     next_states = np.array([np.array(next_state) for _, _, _, next_state, _ in mini_sample])
    #     dones = np.array([done for _, _, _, _, done in mini_sample])
        
    #     self.trainer.train_step(states, actions, rewards, next_states, dones)

    # def train_short_memory(self, state, action, reward, next_state, done):
    #     self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state, board: Board) -> tuple[int, int, int]:
        """
        Returns a tuple of (action_type, target_player_id, card_to_reveal)
        action_type: 0 for revenue, 1 for coup
        target_player_id: -1 for revenue, 0-3 for assassination target
        card_to_reveal: -1 for no reveal, 0-1 for card index to reveal
        """
        player = board.players[self.player_id]
        
        # Random moves: tradeoff exploration / exploitation
        # self.epsilon = 80 - self.n_games
        # if random.randint(0, 200) < self.epsilon:

        # Random action
        # Check if assassination is possible
        possible_targets = [p.id for p in board.alive_players 
                            if p.id != player.id and any(not card.is_revealed for card in p.hand)]
        
        if player.can_coup and possible_targets:
            action_type = random.choice([0, 1])  # Can either take revenue or coup
        else:
            action_type = 0  # Can only take revenue
            
        # If assassinating, choose random target
        target_player_id = -1
        if action_type == 1 and possible_targets:
            target_player_id = random.choice(possible_targets)
            
        # If we need to reveal a card, choose randomly
        card_to_reveal = -1
        if player.nb_remaining_cards > 1:  # If we have multiple cards to choose from
            unrevealed_cards = [i for i, card in enumerate(player.hand) if not card.is_revealed]
            if unrevealed_cards:
                card_to_reveal = random.choice(unrevealed_cards)
                
        return action_type, target_player_id, card_to_reveal
        
        # else:
        #     # Get action from model
        #     state0 = torch.from_numpy(state).float()
        #     prediction = self.model(state0.unsqueeze(0))
            
        #     # Convert model output to action
        #     action_idx = torch.argmax(prediction).item()
            
        #     # Decode action index into components
        #     # First 2 indices are action types
        #     action_type = 0 if action_idx < 2 else 1
            
        #     # Next 3 indices are target players
        #     target_player_id = (action_idx - 2) % 3 if action_type == 1 else -1
            
        #     # Last 2 indices are card reveals
        #     card_to_reveal = (action_idx - 5) if action_idx >= 5 else -1
            
        #     return action_type, target_player_id, card_to_reveal

# class Linear_QNet(torch.nn.Module):
#     def __init__(self, input_size, hidden_size, output_size):
#         super().__init__()
#         self.linear1 = torch.nn.Linear(input_size, hidden_size)
#         self.linear2 = torch.nn.Linear(hidden_size, output_size)

#     def forward(self, x):
#         x = torch.nn.functional.relu(self.linear1(x))
#         x = self.linear2(x)
#         return x

#     def save(self, file_name='model.pth'):
#         torch.save(self.state_dict(), file_name)

# class QTrainer:
#     def __init__(self, model, lr, gamma):
#         self.model = model
#         self.lr = lr
#         self.gamma = gamma
#         self.optimizer = torch.optim.Adam(model.parameters(), lr=self.lr)
#         self.criterion = torch.nn.MSELoss()

#     def train_step(self, state, action, reward, next_state, done):
#         # Convert to numpy arrays first
#         if isinstance(state, list):
#             state = np.array(state)
#         if isinstance(next_state, list):
#             next_state = np.array(next_state)
#         if isinstance(action, list):
#             action = np.array(action)
#         if isinstance(reward, list):
#             reward = np.array(reward)

#         # Convert to tensors
#         state = torch.from_numpy(state).float()
#         next_state = torch.from_numpy(next_state).float()
#         action = torch.from_numpy(np.array(action)).long()
#         reward = torch.tensor(reward).float()

#         if len(state.shape) == 1:
#             # (1, x)
#             state = torch.unsqueeze(state, 0)
#             next_state = torch.unsqueeze(next_state, 0)
#             action = torch.unsqueeze(action, 0)
#             reward = torch.unsqueeze(reward, 0)
#             done = (done, )

#         # 1: predicted Q values with current state
#         pred = self.model(state)

#         target = pred.clone()
#         for idx in range(len(done)):
#             Q_new = reward[idx]
#             if not done[idx]:
#                 Q_new = reward[idx] + self.gamma * torch.max(self.model(next_state[idx]))

#             target[idx][torch.argmax(action[idx]).item()] = Q_new
    
#         # 2: Q_new = r + y * max(next_predicted Q value)
#         self.optimizer.zero_grad()
#         loss = self.criterion(target, pred)
#         loss.backward()
#         self.optimizer.step()
