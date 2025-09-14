import random
from action import Action, ActionType
from card import Card
from player import Player


class CoupAgent:
    def __init__(self, player: Player):
        self.player = player
        self.state = None

    def choose_card_to_reveal(self, hand: list[Card]) -> Card:
        return random.choice([c for c in hand if not c.is_revealed])

    def get_desired_action(self, player: Player, alive_players: list[Player]) -> Action:
        # Random choice from available actions TODO implement RL logic later
        possible_targets = [
            p.id
            for p in alive_players
            if p.id != self.player.id and any(not card.is_revealed for card in p.hand)
        ]
        coup_actions = [
            Action(
                action_type=ActionType.COUP,
                origin_player_id=self.player.id,
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
        foreign_aid_action = Action(
            action_type=ActionType.FOREIGN_AID,
            origin_player_id=player.id,
            target_player_id=-1,
            card_to_reveal=-1,
            can_be_countered=True,
            can_be_challenged=False,
        )
        if player.must_coup:
            available_actions = coup_actions
        elif player.can_coup and possible_targets:
            available_actions = coup_actions + [
                revenue_action,
                foreign_aid_action,
            ]
        else:
            available_actions = [revenue_action, foreign_aid_action]
        desired_action = random.choice(available_actions)
        return desired_action

    def get_desired_challenge(
        self,
        action_to_challenge: Action,  # will be used later with RL logic
        player_to_challenge: Player,
    ) -> Action:
        available_actions = [
            Action(
                action_type=ActionType.CHALLENGE,
                origin_player_id=self.player.id,
                target_player_id=player_to_challenge.id,
                can_be_countered=False,
                can_be_challenged=False,
                card_to_reveal=-1,
            ),
            Action(
                action_type=ActionType.DO_NOTHING,
                origin_player_id=self.player.id,
                target_player_id=player_to_challenge.id,
                card_to_reveal=-1,
                can_be_countered=False,
                can_be_challenged=False,
            ),
        ]
        desired_challenge = random.choice(available_actions)
        return desired_challenge

    def get_desired_counter(
        self,
        action_to_counter: Action,  # will be used later with RL logic
        player_to_counter: Player,
    ) -> Action:
        available_actions = [
            Action(
                action_type=ActionType.DO_NOTHING,
                origin_player_id=self.player.id,
                target_player_id=player_to_counter.id,
                card_to_reveal=-1,
                can_be_countered=False,
                can_be_challenged=False,
            ),
        ]
        if action_to_counter.action_type == ActionType.FOREIGN_AID:
            available_actions.append(
                Action(
                    action_type=ActionType.COUNTER_FOREIGN_AID_WITH_DUKE,
                    origin_player_id=self.player.id,
                    target_player_id=player_to_counter.id,
                    card_to_reveal=-1,
                    can_be_countered=False,
                    can_be_challenged=True,
                )
            )
        desired_counter = random.choice(available_actions)
        return desired_counter
