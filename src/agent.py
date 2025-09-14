import random
from action import Action, ActionType
from player import Player


class CoupAgent:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.state = None

    def get_desired_action(self, player: Player, alive_players: list[Player]) -> Action:
        # Random choice from available actions TODO implement RL logic later
        possible_targets = [
            p.id
            for p in alive_players
            if p.id != player.id and any(not card.is_revealed for card in p.hand)
        ]
        coup_actions = [
            Action(
                action_type=ActionType.COUP,
                origin_player_id=player.id,
                target_player_id=target_player_id,
                card_to_reveal=-1,
                can_be_countered=False,
                can_be_challenged=False,
            )
            for target_player_id in possible_targets
        ]
        revenue_action = Action(
            action_type=ActionType.REVENUE,
            origin_player_id=player.id,
            target_player_id=-1,
            card_to_reveal=-1,
            can_be_countered=False,
            can_be_challenged=False,
        )
        duke_action = Action(
            action_type=ActionType.DUKE,
            origin_player_id=player.id,
            target_player_id=-1,
            card_to_reveal=-1,
            can_be_countered=False,
            can_be_challenged=False,
        )
        if player.must_coup:
            available_actions = coup_actions
        elif player.can_coup and possible_targets:
            available_actions = coup_actions + [revenue_action] + [duke_action]
        else:
            available_actions = [duke_action]
        desired_action = random.choice(available_actions)
        print(desired_action)
        return desired_action

    def get_desired_challenge(
        self, player: Player, player_to_challenge: Player
    ) -> Action:
        available_actions = [
            Action(
                action_type=ActionType.CHALLENGE,
                origin_player_id=player.id,
                target_player_id=player_to_challenge.id,
                card_to_reveal=-1,
            ),
            Action(
                action_type=ActionType.DO_NOTHING,
                origin_player_id=player.id,
                target_player_id=player_to_challenge.id,
                card_to_reveal=-1,
            ),
        ]
        desired_challenge = random.choice(available_actions)
        return desired_challenge
