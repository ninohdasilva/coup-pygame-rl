import random
import numpy as np
from action import Action, ActionType
from card import Card
from character import Character
from player import Player
from deck import Deck
from agent import CoupAgent
from pydantic import BaseModel


class ActionHistoryItem(BaseModel):
    origin_player: Player
    target_player: Player
    action_type: ActionType


class DeckHistoryItem(BaseModel):
    card: Card
    returned_from: bool
    given_to: bool
    player: Player
    public: bool


class Board:
    nb_players: int
    players: list[Player]
    agents: list[CoupAgent]
    alive_players: list[Player]
    current_player: Player
    deck: Deck
    game_has_started: bool
    game_has_ended: bool
    state_item_length = 128
    state_item_width = 64
    agents_states: np.ndarray
    actions_history: list[ActionHistoryItem]
    deck_history: list[DeckHistoryItem]

    def __init__(self, nb_players: int = 4):
        self.nb_players = nb_players
        self.players = []
        self.agents = []
        self.current_player = None
        self.game_has_started = False
        self.game_has_ended = True

    def get_player_by_id(self, id: int):
        return self.players[id]

    def return_card_from_player_to_deck(self, card: Card, player: Player, public=False):
        self.deck.add_card(card)
        player.lose_card(card)
        self.deck_history.append(
            DeckHistoryItem(
                card=card,
                returned_from=True,
                given_to=False,
                player=player,
                public=public,
            )
        )
        self.deck_history = self.deck_history[-self.state_item_length :]

    def draw_single_card_from_deck_to_player(self, player: Player):
        player.hand.append(self.deck.draw())
        self.deck_history.append(
            DeckHistoryItem(
                card=player.hand[-1],
                returned_from=False,
                given_to=True,
                player=player,
                public=False,
            )
        )
        self.deck_history = self.deck_history[-self.state_item_length :]

    def start(self):
        self.game_has_started = True
        self.game_has_ended = False
        self.deck = Deck()
        self.deck.shuffle()
        # Clear existing players
        self.players = []
        # Create new players
        for i in range(self.nb_players):
            player = Player(
                id=i,
                name=f"Player {i}",
                hand=self.deck.draw(2),
                coins=2,
                can_coup=False,
                must_coup=False,
                is_alive=True,
                nb_remaining_cards=2,
            )
            self.players.append(player)
        self.alive_players = self.players.copy()
        self.agents = [CoupAgent(player) for player in self.players]
        for agent in self.agents:
            agent.player.agent_id = agent.id
        self.current_player = random.choice(self.alive_players)
        self.actions_history = []
        self.deck_history = []

    def extend_actions_history(self, action: Action):
        self.actions_history.append(
            ActionHistoryItem(
                origin_player=self.get_player_by_id(action.origin_player_id),
                target_player=self.get_player_by_id(action.target_player_id),
                action_type=action.action_type,
            )
        )
        self.actions_history = self.actions_history[-self.state_item_length :]

    def extend_deck_history(
        self,
        card: Card,
        returned_from: bool,
        given_to: bool,
        player: Player,
        visibility: list[Player],
    ):
        self.deck_history.append(
            DeckHistoryItem(
                card=card,
                returned_from=returned_from,
                given_to=given_to,
                player=player,
                visibility=visibility,
            )
        )
        self.deck_history = self.deck_history[-self.state_item_length :]

    def update_agent_states(self):
        """Convert the game state into a numerical representation"""
        deck_size_vector = np.array(
            [
                0 if i != len(self.deck.deck) else 1
                for i in range(self.state_item_width // 4)
            ]
        )
        nb_players_vector = np.array(
            [
                0 if i != len(self.players) else 1
                for i in range(self.state_item_width // 4)
            ]
        )
        player_coins_vectors = np.concatenate(
            [
                [
                    0 if i != player.coins else 1
                    for i in range(self.state_item_width // 4)
                ]
                for player in self.players
            ]
        )
        players_alive_status_vectors = np.concatenate(
            [
                [
                    1 if i == player.id and player.is_alive else 0
                    for i in range(self.state_item_width // 4)
                ]
                for player in self.players
            ]
        )

        # Public player hands
        # All players will see the same in their state
        # Represents what would be visibile to an external observer
        public_player_hands = []
        for player in self.players:
            hand_representation = []
            for card in player.hand:
                if not card.is_revealed:
                    hand_representation += [
                        1 if i == 0 else 0 for i in range(self.state_item_width // 4)
                    ]
                else:
                    hand_representation += [
                        0 if i != card.character.to_int() else 1
                        for i in range(self.state_item_width // 4)
                    ]
            public_player_hands.append(
                np.concatenate(
                    [
                        hand_representation,
                        np.zeros(self.state_item_width // 2),
                    ]
                )
            )
        public_player_hands = np.stack(public_player_hands)
        # Private player hands, all cards are revealed for each hand
        # We create a dict so that players will only see their own hand in their state
        private_player_hands = {}
        for player in self.players:
            hand_representation = []
            for card in player.hand:
                if not card.is_revealed:
                    hand_representation += [
                        1 if i == 0 else 0 for i in range(self.state_item_width // 4)
                    ]
                else:
                    hand_representation += [
                        0 if i != card.character.to_int() else 1
                        for i in range(self.state_item_width // 4)
                    ]
            private_player_hands[player.id] = np.concatenate(
                [hand_representation, np.zeros(self.state_item_width // 2)],
            )

        # Create actions history with proper shape (state_item_length x state_item_width)
        actions_history = []
        for action in self.actions_history:
            # Create one-hot vectors for each component
            origin_vector = [
                0 if i != action.origin_player.id else 1
                for i in range(self.state_item_width // 4)
            ]
            action_type_vector = [
                0 if i != action.action_type.value else 1
                for i in range(self.state_item_width // 4)
            ]
            target_vector = [
                0 if i != action.target_player.id else 1
                for i in range(self.state_item_width // 4)
            ]

            # Combine the vectors while maintaining state_item_width dimension
            action_representation = np.concatenate(
                [
                    origin_vector,
                    action_type_vector,
                    target_vector,
                    np.zeros(self.state_item_width // 4),
                ]
            )  # shape: (state_item_width,)
            actions_history.append(action_representation)

        # Convert to numpy array and ensure proper shape
        actions_history = (
            np.array(actions_history)
            if actions_history
            else np.zeros((0, self.state_item_width))
        )
        # Deck history with proper shape (n, state_item_width)
        public_deck_history = []
        for item in self.deck_history:
            if item.public:
                card_representation = [
                    1 if i != item.card.character.to_int() else 0
                    for i in range(self.state_item_width // 4)
                ]
            else:
                card_representation = [
                    1 if i == 0 else 0 for i in range(self.state_item_width // 4)
                ]
            returned_from_or_given_to_vector = [
                0 if i != item.returned_from else 1
                for i in range(self.state_item_width // 4)
            ]
            player_vector = [
                0 if i != item.player.id else 1
                for i in range(self.state_item_width // 4)
            ]
            public_deck_history.append(
                np.concatenate(
                    card_representation,
                    returned_from_or_given_to_vector,
                    player_vector,
                    np.zeros(self.state_item_width // 4),
                )
            )

        # Convert to numpy array with proper shape
        public_deck_history = (
            np.array(public_deck_history)
            if public_deck_history
            else np.zeros((0, self.state_item_width))
        )
        # Like private player hands, each deck history item where the player has not seen the card has hidden card representation
        private_deck_history = {}
        for player in self.players:
            private_deck_history[player.id] = []
            for item in self.deck_history:
                # Create card representation
                if item.player.id == player.id:
                    card_representation = [
                        1 if i != item.card.character.to_int() else 0
                        for i in range(self.state_item_width // 4)
                    ]
                else:
                    card_representation = [
                        1 if i == 0 else 0 for i in range(self.state_item_width // 4)
                    ]
                returned_from_or_given_to_vector = [
                    0 if i != item.returned_from else 1
                    for i in range(self.state_item_width // 4)
                ]
                player_vector = [
                    0 if i != item.player.id else 1
                    for i in range(self.state_item_width // 4)
                ]

                # Convert to numpy array and append
                private_deck_history[player.id].append(np.array(card_representation))

            # Convert list to numpy array with proper shape
            if private_deck_history[player.id]:
                # Stack arrays and verify shape
                private_deck_history[player.id] = np.array(
                    private_deck_history[player.id]
                )
                assert (
                    private_deck_history[player.id].shape[1]
                    == self.state_item_width // 4
                ), (
                    f"private_deck_history shape mismatch for player {player.id}: "
                    f"{private_deck_history[player.id].shape}"
                )
            else:
                # Initialize with empty array of proper shape
                private_deck_history[player.id] = np.zeros((0, self.state_item_width))

        deck_size_plus_nb_players_vectors = np.concatenate(
            [deck_size_vector, nb_players_vector, np.zeros(self.state_item_width // 2)]
        )

        board_info = np.stack(
            [
                deck_size_plus_nb_players_vectors,
                player_coins_vectors,
                players_alive_status_vectors,
            ]
        )

        padded_actions_history = np.vstack(
            [
                actions_history.squeeze(),
                np.zeros(
                    (
                        self.state_item_length - len(actions_history),
                        self.state_item_width,
                    )
                ),
            ]
        )
        for agent in self.agents:
            player_hands = np.vstack(
                [
                    public_player_hands,
                    private_player_hands[agent.player.id],
                ]
            )

            padded_public_deck_history = np.vstack(
                [
                    public_deck_history,
                    np.zeros(
                        (
                            self.state_item_length - len(public_deck_history),
                            self.state_item_width,
                        )
                    ),
                ]
            )
            # Handle private deck history padding
            if len(private_deck_history[agent.player.id]) > 0:
                # If we have history, pad it to state_item_length
                padded_private_deck_history = np.concatenate(
                    [
                        private_deck_history[agent.player.id],
                        np.zeros(
                            (
                                self.state_item_length
                                - private_deck_history[agent.player.id].shape[0],
                                self.state_item_width,
                            )
                        ),
                    ]
                )
            else:
                # If no history, create empty array with proper shape
                padded_private_deck_history = np.zeros(
                    (self.state_item_length, self.state_item_width)
                )
            # Verify shapes before concatenation
            assert board_info.shape[1] == self.state_item_width, (
                f"board_info shape mismatch: {board_info.shape}"
            )
            assert player_hands.shape[1] == self.state_item_width, (
                f"player_hands shape mismatch: {player_hands.shape}"
            )
            assert padded_actions_history.shape[1] == self.state_item_width, (
                f"padded_actions_history shape mismatch: {padded_actions_history.shape}"
            )
            assert padded_public_deck_history.shape[1] == self.state_item_width, (
                f"padded_public_deck_history shape mismatch: {padded_public_deck_history.shape}"
            )
            assert padded_private_deck_history.shape[1] == self.state_item_width, (
                f"padded_private_deck_history shape mismatch: {padded_private_deck_history.shape}"
            )

            # Concatenate along first axis (stacking vertically)
            agent.state = np.vstack(
                [
                    board_info,
                    player_hands,
                    padded_actions_history,
                    padded_public_deck_history,
                    padded_private_deck_history,
                ]
            )

    def check_if_game_has_ended(self):
        # Find next alive player before updating alive status else IndexError
        # print(
        #     f"Alive players before update: {[('player.is_alive', player.is_alive, player.name, player.coins, [('is_revealed', card.is_revealed) for card in player.hand]) for player in self.alive_players]}"
        # )
        # print(f"Current player: {self.current_player.name}")
        # Update alive status for each player
        for player in self.players:
            player.is_alive = any(not card.is_revealed for card in player.hand)
            if not player.is_alive:
                player.coins = 0

        # Update alive players list
        self.alive_players = [player for player in self.players if player.is_alive]
        # print(
        #     f"Alive players after update: {[('player.is_alive', player.is_alive, player.name, player.coins, [('is_revealed', card.is_revealed) for card in player.hand]) for player in self.alive_players]}"
        # )

        found_next_player = False
        while not found_next_player:
            current_position = self.players.index(self.current_player)
            next_position = (current_position + 1) % len(self.players)
            self.current_player = self.players[next_position]
            if self.current_player.is_alive:
                found_next_player = True
        # print(f"Next player: {self.current_player.name}")

        # Game ends when only one player has unrevealed cards
        if len(self.alive_players) == 1:
            self.game_has_ended = True
            self.game_has_started = False
            return True

        return False

    def execute_action(
        self, agent: CoupAgent, player: Player, action: Action, last_actions: list[str]
    ):
        if not action.can_be_challenged and not action.can_be_countered:
            # Revenue
            if action.action_type == ActionType.REVENUE:
                player.get_revenue()
                last_actions.append(f"{player.name} collected 1 coin with revenue")
                self.extend_actions_history(action)
                self.update_agent_states()
            # Coup
            elif action.action_type == ActionType.COUP:
                target_player = self.get_player_by_id(action.target_player_id)
                target_player_agent = self.agents[target_player.agent_id]
                target_player_agent.choose_card_to_reveal(target_player.hand)
                player.pay_coup(target_player)
                last_actions.append(
                    f"{player.name} launched a Coup on {target_player.name}"
                )
                self.extend_actions_history(action)
                self.update_agent_states()
        else:
            if action.can_be_challenged:
                last_action = f"{player.name} tries to use {action.action_type}"
                if action.target_player_id != -1:
                    last_action += (
                        f" on {self.get_player_by_id(action.target_player_id).name}"
                    )
                last_actions.append(last_action)
                self.extend_actions_history(action)
                self.update_agent_states()
                # Get eventual challenges
                challenges = [
                    agent.choose_challenge(
                        player, self.get_player_by_id(agent.player.id)
                    )
                    for agent in self.agents
                    if agent.player.id != player.id
                ]
                challenges = [
                    action
                    for action in challenges
                    if action.action_type == ActionType.CHALLENGE
                ]
                if challenges:
                    action.can_be_countered = False  # Action that is challenged cannot be countered afterwards
                    # Select a challenge
                    selected_challenge = random.choice(challenges)
                    challenging_player = self.get_player_by_id(
                        selected_challenge.origin_player_id
                    )
                    challenging_player_agent = self.agents[challenging_player.agent_id]
                    last_actions.append(
                        f"{challenging_player.name} is challenging {action.action_type} by {player.name}"
                    )
                    self.extend_actions_history(selected_challenge)
                    self.update_agent_states()
                    is_bluffing, action_card = player.is_bluffing(action)
                    # Challenge successful
                    if is_bluffing:
                        agent.choose_card_to_reveal(player.hand)
                        # Player still pays for failed assassin action
                        if action.action_type == ActionType.ASSASSIN:
                            player.lose_coins(3)
                        last_actions.append(
                            f"{player.name} was bluffing action {action.action_type} and lost an influence"
                        )
                        self.update_agent_states()  # No action because it has failed due to the challenge
                    # Challenge failed
                    else:
                        challenging_player_agent.choose_card_to_reveal(
                            challenging_player.hand
                        )
                        last_actions.append(
                            f"{challenging_player.name} lost his challenge and lost an influence"
                        )
                        # Player draws new card
                        self.return_card_from_player_to_deck(action_card, player)
                        self.draw_single_card_from_deck_to_player(player)
                        # Action is executed
                        if action.action_type == ActionType.DUKE:
                            player.gain_coins(3)
                            player.update_coup_status()
                            last_actions.append(
                                f"{player.name} gained 3 coins with duke"
                            )
                        elif action.action_type == ActionType.CAPTAIN:
                            target_player = self.get_player_by_id(
                                action.target_player_id
                            )
                            target_player.lose_coins(2)
                            player.gain_coins(2)
                            player.update_coup_status()
                            last_actions.append(
                                f"{player.name} successfully stole 2 coins from {target_player.name} with action {action.action_type}"
                            )
                        elif action.action_type == ActionType.ASSASSIN:
                            target_player = self.get_player_by_id(
                                action.target_player_id
                            )
                            target_player_agent = self.agents[target_player.agent_id]
                            target_player_agent.choose_card_to_reveal(
                                target_player.hand
                            )
                            player.pay_assassin()
                            last_actions.append(
                                f"{player.name} successfully assassinated {target_player.name} with action {action.action_type}"
                            )
                        elif action.action_type == ActionType.AMBASSADOR:
                            drawn_cards = self.deck.draw(2)
                            unused_cards = agent.choose_cards_to_keep_after_ambassador(
                                player.hand, drawn_cards
                            )
                            for card in unused_cards:
                                self.return_card_from_player_to_deck(card, player)
                            last_actions.append(
                                f"{player.name} successfully exchanged 2 cards with action {action.action_type}"
                            )
                        self.extend_actions_history(
                            action
                        )  # maybe we will need to create a specific action instead of repeating
                        self.update_agent_states()

            if action.can_be_countered:
                # Get eventual counters
                last_actions.append(f"{player.name} tries to use {action.action_type}")
                counters = [
                    agent.choose_counter(
                        action_to_counter=action,
                        player_to_counter=agent.player,
                    )
                    for agent in self.agents
                    if agent.player.id != player.id
                ]
                counters = [
                    action
                    for action in counters
                    if action.action_type != ActionType.DO_NOTHING
                ]
                if counters:
                    # Select a counter
                    selected_counter = random.choice(counters)
                    countering_player = self.get_player_by_id(
                        selected_counter.origin_player_id
                    )
                    countering_player_agent = self.agents[countering_player.agent_id]
                    last_actions.append(
                        f"{countering_player.name} tries to counter {player.name} with {selected_counter.action_type}"
                    )
                    self.extend_actions_history(selected_counter)
                    self.update_agent_states()
                    # All counters can be challenged
                    challenge = agent.choose_challenge(
                        action_to_challenge=action,
                        player_to_challenge=countering_player,
                    )
                    # Player challenges countering player
                    if challenge.action_type == ActionType.CHALLENGE:
                        last_actions.append(
                            f"{player.name} is challenging {countering_player.name} with {challenge.action_type}"
                        )
                        self.extend_actions_history(challenge)
                        self.update_agent_states()
                        is_bluffing, countering_card = countering_player.is_bluffing(
                            selected_counter
                        )
                        # Challenge successful
                        if is_bluffing:
                            countering_player_agent.choose_card_to_reveal(
                                countering_player.hand
                            )
                            last_actions.append(
                                f"{countering_player.name} was bluffing for his counter and lost an influence"
                            )
                            # Player original action is executed
                            if action.action_type == ActionType.FOREIGN_AID:
                                player.get_foreign_aid()
                                last_actions.append(
                                    f"{player.name} successfully collected 2 coins with foreign aid"
                                )
                            elif action.action_type == ActionType.CAPTAIN:
                                target_player = self.get_player_by_id(
                                    action.target_player_id
                                )
                                target_player.lose_coins(2)
                                player.gain_coins(2)
                                player.update_coup_status()
                                last_actions.append(
                                    f"{player.name} successfully stole 2 coins from {target_player.name} with CAPTAIN"
                                )
                            self.extend_actions_history(action)
                            self.update_agent_states()
                        # Challenge failed
                        else:
                            # Player loses an influence
                            agent.choose_card_to_reveal(player.hand)
                            last_actions.append(
                                f"{player.name} lost his challenge and lost an influence"
                            )
                            # Countering player draws new card
                            self.return_card_from_player_to_deck(
                                countering_card, countering_player
                            )
                            self.draw_single_card_from_deck_to_player(countering_player)
                            last_actions.append(
                                f"{countering_player.name} successfully countered {action.action_type} from {player.name}"
                            )
                            self.update_agent_states()
                    # Player does not challenge countering player
                    else:
                        last_actions.append(
                            f"{countering_player.name} successfully countered {action.action_type} from {player.name}"
                        )
                        self.update_agent_states()

                # Action is not countered
                else:
                    if action.action_type == ActionType.FOREIGN_AID:
                        player.get_foreign_aid()
                        last_actions.append(
                            f"{player.name} successfully collected 2 coins with foreign aid"
                        )
                    elif action.action_type == ActionType.CAPTAIN:
                        target_player = self.get_player_by_id(action.target_player_id)
                        target_player.lose_coins(2)
                        player.gain_coins(2)
                        player.update_coup_status()
                        last_actions.append(
                            f"{player.name} successfully stole 2 coins from {target_player.name} with CAPTAIN"
                        )
                    elif action.action_type == ActionType.ASSASSIN:
                        target_player = self.get_player_by_id(action.target_player_id)
                        target_player_agent = self.agents[target_player.agent_id]
                        target_player_agent.choose_card_to_reveal(target_player.hand)
                        player.pay_assassin()
                        last_actions.append(
                            f"{player.name} successfully assassinated {target_player.name} with ASSASSIN"
                        )
                    elif action.action_type == ActionType.AMBASSADOR:
                        drawn_cards = self.deck.draw(2)
                        unused_cards = agent.choose_cards_to_keep_after_ambassador(
                            player.hand, drawn_cards
                        )
                        for card in unused_cards:
                            self.return_card_from_player_to_deck(card, player)
                        last_actions.append(
                            f"{player.name} successfully exchanged 2 cards with AMBASSADOR"
                        )
                        self.update_agent_states()
        return last_actions

    def agents_next_move(self, last_actions: list[str], last_actions_max_length: int):
        if self.check_if_game_has_ended():
            return []

        # Get current player and their agent
        current_player = self.current_player
        current_agent = self.agents[current_player.id]

        # Get state and desired action from agent
        chosen_action = current_agent.choose_action(current_player, self.alive_players)

        # Execute action and update states
        last_actions = self.execute_action(
            agent=current_agent,
            player=current_player,
            action=chosen_action,
            last_actions=last_actions,
        )
        while len(last_actions) > last_actions_max_length:
            last_actions.pop(0)
        # print(f"Last actions: {last_actions}")
        for agent in self.agents:
            # print(f"Agent {agent.player.name} state: {agent.state}")
            print(agent.state.shape)

        # if self.check_if_game_has_ended():
        #     return []

        return last_actions
