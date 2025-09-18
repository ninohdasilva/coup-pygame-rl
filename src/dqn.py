import torch
import random
import torch.nn as nn
import torch.nn.functional as F


class DQN(nn.Module):
    def __init__(
        self,
        full_state_length,
        state_item_width,
        n_actions,
        hidden_dim=256,
    ):
        super().__init__()
        input_dim = full_state_length * state_item_width  # flatten (392,64) → ~25k
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, n_actions)

    def forward(self, x):
        # x: [batch, length, width]
        x = x.flatten()  # flatten per batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)  # [batch, n_actions]

    def select_action(self, state, action_mask, device):
        state = torch.tensor(state, dtype=torch.float).to(device)
        action_mask = action_mask.to(device)
        action = self.forward(state)
        return action
