import random
import torch
from action import Action, ActionType
from card import Card
from character import Character
from player import Player
from dqn import DQN


class CoupAgent:
    def __init__(
        self,
        player: Player,
        full_state_length: int,
        state_item_width: int,
        epsilon: float = 0.1,
    ):
        self.id = player.id
        self.player = player
        self.state = None
        self.n_actions = len(ActionType)
        self.epsilon = epsilon
        self.device = "cpu"

        self.policy_net = DQN(full_state_length, state_item_width, self.n_actions).to(
            self.device
        )
        self.target_net = DQN(full_state_length, state_item_width, self.n_actions).to(
            self.device
        )
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

    def get_coup_action_type_from_target_player_id(
        self, target_player_id: int
    ) -> ActionType:
        if target_player_id == 0:
            return ActionType.COUP_TARGET_PLAYER_0
        elif target_player_id == 1:
            return ActionType.COUP_TARGET_PLAYER_1
        elif target_player_id == 2:
            return ActionType.COUP_TARGET_PLAYER_2
        elif target_player_id == 3:
            return ActionType.COUP_TARGET_PLAYER_3
        else:
            return ValueError(f"Invalid target player id: {target_player_id}")

    def get_captain_action_type_from_target_player_id(
        self, target_player_id: int
    ) -> ActionType:
        if target_player_id == 0:
            return ActionType.CAPTAIN_TARGET_PLAYER_0
        elif target_player_id == 1:
            return ActionType.CAPTAIN_TARGET_PLAYER_1
        elif target_player_id == 2:
            return ActionType.CAPTAIN_TARGET_PLAYER_2
        elif target_player_id == 3:
            return ActionType.CAPTAIN_TARGET_PLAYER_3
        else:
            return ValueError(f"Invalid target player id: {target_player_id}")

    def get_assassin_action_type_from_target_player_id(
        self, target_player_id: int
    ) -> ActionType:
        if target_player_id == 0:
            return ActionType.ASSASSIN_TARGET_PLAYER_0
        elif target_player_id == 1:
            return ActionType.ASSASSIN_TARGET_PLAYER_1
        elif target_player_id == 2:
            return ActionType.ASSASSIN_TARGET_PLAYER_2
        elif target_player_id == 3:
            return ActionType.ASSASSIN_TARGET_PLAYER_3
        else:
            return ValueError(f"Invalid target player id: {target_player_id}")

    def create_action_mask(self, available_actions: list[ActionType]) -> torch.tensor:
        return torch.tensor(
            [
                1
                if any(
                    action.action_type == ActionType(i) for action in available_actions
                )
                else 0
                for i in range(len(ActionType))
            ]
        )

    def select_action(
        self,
        state: torch.tensor,
        action_mask: torch.tensor,
        available_actions: list[ActionType],
    ) -> ActionType:
        # if random.random() < self.epsilon:
        #     # explore: choose random valid action
        #     valid_actions = torch.nonzero(action_mask[0], as_tuple=True)[0]
        #     action_type_value = valid_actions[
        #         torch.randint(len(valid_actions), (1,))
        #     ].item()
        # else:
        # exploit: mask Q-values
        print(f"action_mask: {action_mask}")
        with torch.no_grad():
            q_values = self.policy_net.select_action(
                state, action_mask, self.device
            )  # [1, n_actions]
            invalid_value = -1e9
            masked_q_values = q_values + (action_mask == 0) * invalid_value
            action_type_value = masked_q_values.argmax(dim=0).item()

        print(f"action_type_value: {action_type_value}")
        # convert model choice to action instead of int
        for action_type in ActionType:
            if action_type.value == action_type_value:
                print(f"action_type: {action_type}")
                for action in available_actions:
                    if action.action_type == action_type:
                        return action

    def choose_card_to_reveal(self, hand: list[Card]) -> Card:
        if any(not card.is_revealed for card in hand):
            available_actions = []
            for i in range(2):
                if not hand[i].is_revealed:
                    if i == 0:
                        action_type = ActionType.REVEAL_CARD_1
                    else:
                        action_type = ActionType.REVEAL_CARD_2
                    available_actions.append(
                        Action(
                            action_type=action_type,
                            origin_player_id=self.player.id,
                            target_player_id=-1,
                            can_be_countered=False,
                            can_be_challenged=False,
                        )
                    )
            action_mask = self.create_action_mask(available_actions)
            action = self.select_action(self.state, action_mask, available_actions)
            return action
        else:
            return ValueError("No card to reveal")

    def choose_card_to_discard(self, hand: list[Card]) -> Card:
        available_actions = []
        for card in hand:
            if not card.is_revealed:
                if card.character == Character.CAPTAIN:
                    available_actions.append(ActionType.DISCARD_CAPTAIN)
                elif card.character == Character.AMBASSADOR:
                    available_actions.append(ActionType.DISCARD_AMBASSADOR)
                elif card.character == Character.ASSASSIN:
                    available_actions.append(ActionType.DISCARD_ASSASSIN)
                elif card.character == Character.DUKE:
                    available_actions.append(ActionType.DISCARD_DUKE)
                elif card.character == Character.CONTESSA:
                    available_actions.append(ActionType.DISCARD_CONTESSA)
        available_actions = list(set(available_actions))
        if available_actions:
            action_mask = self.create_action_mask(available_actions)
            action = self.select_action(self.state, action_mask, available_actions)
            card = None
            if action == ActionType.DISCARD_CAPTAIN:
                for card in self.player.hand:
                    if card.character == Character.CAPTAIN:
                        card = card
                        break
            elif action == ActionType.DISCARD_AMBASSADOR:
                for card in self.player.hand:
                    if card.character == Character.AMBASSADOR:
                        card = card
                        break
            elif action == ActionType.DISCARD_ASSASSIN:
                for card in self.player.hand:
                    if card.character == Character.ASSASSIN:
                        card = card
                        break
            elif action == ActionType.DISCARD_DUKE:
                for card in self.player.hand:
                    if card.character == Character.DUKE:
                        card = card
                        break
            elif action == ActionType.DISCARD_CONTESSA:
                for card in self.player.hand:
                    if card.character == Character.CONTESSA:
                        card = card
                        break
            return action, card
        else:
            return ValueError("No card to discard")

    def choose_action(self, player: Player, alive_players: list[Player]) -> Action:
        # Random choice from available actions TODO implement RL logic later
        possible_coup_and_assassin_targets = [
            p.id
            for p in alive_players
            if p.id != self.player.id and any(not card.is_revealed for card in p.hand)
        ]
        possible_captain_targets = [
            p.id
            for p in alive_players
            if p.id != self.player.id
            and any(not card.is_revealed for card in p.hand)
            and p.coins >= 2
        ]
        coup_actions = [
            Action(
                action_type=self.get_coup_action_type_from_target_player_id(
                    target_player_id
                ),
                origin_player_id=self.player.id,
                target_player_id=target_player_id,
                can_be_countered=False,
                can_be_challenged=False,
            )
            for target_player_id in possible_coup_and_assassin_targets
        ]
        captain_actions = [
            Action(
                action_type=self.get_captain_action_type_from_target_player_id(
                    target_player_id
                ),
                origin_player_id=self.player.id,
                target_player_id=-target_player_id,
                can_be_countered=True,
                can_be_challenged=True,
            )
            for target_player_id in possible_captain_targets
        ]
        assassin_actions = [
            Action(
                action_type=self.get_assassin_action_type_from_target_player_id(
                    target_player_id
                ),
                origin_player_id=self.player.id,
                target_player_id=target_player_id,
                can_be_countered=True,
                can_be_challenged=True,
            )
            for target_player_id in possible_coup_and_assassin_targets
        ]
        revenue_action = Action(
            action_type=ActionType.REVENUE,
            origin_player_id=player.id,
            target_player_id=-1,
            can_be_countered=False,
            can_be_challenged=False,
        )
        foreign_aid_action = Action(
            action_type=ActionType.FOREIGN_AID,
            origin_player_id=player.id,
            target_player_id=-1,
            can_be_countered=True,
            can_be_challenged=False,
        )
        available_actions = []
        if player.must_coup:
            available_actions += coup_actions
        else:
            available_actions += [revenue_action, foreign_aid_action]
            if player.can_coup and possible_coup_and_assassin_targets:
                available_actions = coup_actions + [
                    revenue_action,
                    foreign_aid_action,
                ]
                if self.player.coins > 3:
                    available_actions += assassin_actions
            if possible_captain_targets:
                available_actions += captain_actions
        action_mask = self.create_action_mask(available_actions)
        action = self.select_action(self.state, action_mask, available_actions)
        return action

    def choose_challenge(
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
            ),
            Action(
                action_type=ActionType.DO_NOTHING,
                origin_player_id=self.player.id,
                target_player_id=player_to_challenge.id,
                can_be_countered=False,
                can_be_challenged=False,
            ),
        ]
        action_mask = self.create_action_mask(available_actions)
        desired_challenge = self.select_action(
            self.state, action_mask, available_actions
        )
        return desired_challenge

    def choose_counter(
        self,
        action_to_counter: Action,  # will be used later with RL logic
        player_to_counter: Player,
    ) -> Action:
        available_actions = [
            Action(
                action_type=ActionType.DO_NOTHING,
                origin_player_id=self.player.id,
                target_player_id=player_to_counter.id,
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
                    can_be_countered=False,
                    can_be_challenged=True,
                )
            )
        elif action_to_counter.action_type == ActionType.CAPTAIN:
            available_actions.append(
                Action(
                    action_type=ActionType.COUNTER_CAPTAIN_WITH_CAPTAIN,
                    origin_player_id=self.player.id,
                    target_player_id=player_to_counter.id,
                    can_be_countered=False,
                    can_be_challenged=True,
                )
            )
            available_actions.append(
                Action(
                    action_type=ActionType.COUNTER_CAPTAIN_WITH_AMBASSADOR,
                    origin_player_id=self.player.id,
                    target_player_id=player_to_counter.id,
                    can_be_countered=False,
                    can_be_challenged=True,
                )
            )
        elif action_to_counter.action_type == ActionType.ASSASSIN:
            available_actions.append(
                Action(
                    action_type=ActionType.COUNTER_ASSASSIN_WITH_CONTESSA,
                    origin_player_id=self.player.id,
                    target_player_id=player_to_counter.id,
                    can_be_countered=False,
                    can_be_challenged=True,
                )
            )
        action_mask = self.create_action_mask(available_actions)
        desired_counter = self.select_action(self.state, action_mask, available_actions)
        return desired_counter
