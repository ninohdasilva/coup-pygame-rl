import random
import numpy as np
from pydantic import BaseModel
from action import Action, ActionType
from board import Board

class CoupAgentState(BaseModel):
    state: np.ndarray

class CoupAgent:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.state = None

    def get_desired_action(self, board: Board) -> Action:
        player = board.get_player_by_id(self.player_id)

        # Random choice from available actions TODO implement RL logic later
        possible_targets = [p.id for p in board.alive_players 
                            if p.id != player.id and any(not card.is_revealed for card in p.hand)]
        
        if player.must_coup:
            available_actions = [Action(action_type=ActionType.COUP, origin_player_id=player.id, target_player_id=target_player_id, card_to_reveal=-1) for target_player_id in possible_targets]
        elif player.can_coup and possible_targets:
            available_actions = [Action(action_type=ActionType.COUP, origin_player_id=player.id, target_player_id=target_player_id, card_to_reveal=-1) for target_player_id in possible_targets] + [Action(action_type=ActionType.REVENUE, origin_player_id=player.id, target_player_id=-1, card_to_reveal=-1)]
        else:
            available_actions = [Action(action_type=ActionType.REVENUE, origin_player_id=player.id, target_player_id=-1, card_to_reveal=-1)]
        
        desired_action = random.choice(available_actions)
            
        return desired_action

    def get_desired_challenge(self, player_to_challenge_id: int, board: Board) -> Action:
        player = board.get_player_by_id(self.player_id)
        
        available_actions = [Action(action_type=ActionType.CHALLENGE, origin_player_id=player.id, target_player_id=player_to_challenge_id, card_to_reveal=-1), Action(action_type=ActionType.DO_NOTHING, origin_player_id=player.id, target_player_id=player_to_challenge_id, card_to_reveal=-1)]
        
        desired_challenge = random.choice(available_actions)
        return desired_challenge