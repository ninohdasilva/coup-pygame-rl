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

    def __init__(self, nb_players: int = 4):
        self.nb_players = nb_players
        self.players = []
        self.agents = []
        self.next_player = None
        self.game_has_started = False
        self.game_has_ended = True

    def get_player_by_id(self, id: int):
        return self.players[id]

    def return_card_from_player_to_deck(self, card: Card, player: Player):
        self.deck.add_card(card)
        player.lose_card(card)

    def draw_single_card_from_deck_to_player(self, player: Player):
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
        self.next_player = random.choice(self.alive_players)

    def update_states(self, last_actions: list[Action]):
        """Convert the game state into a numerical representation"""
        for agent in self.agents:
            state = []
            player = agent.player

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
                            state.append(
                                1
                                if (card.is_revealed and card.character == char)
                                else 0
                            )
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
        # Find next alive player before updating alive status else IndexError
        current_position = self.alive_players.index(self.next_player)
        next_position = (current_position + 1) % len(self.alive_players)
        self.next_player = self.alive_players[next_position]

        # Update alive status for each player
        for player in self.players:
            player.is_alive = any(not card.is_revealed for card in player.hand)

        # Update alive players list
        self.alive_players = [player for player in self.players if player.is_alive]
        print(f"Alive players: {[player.name for player in self.alive_players]}")

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
                player.action_revenue()
                last_actions.append(f"{player.name} collected 1 coin with revenue")
            # Coup
            elif action.action_type == ActionType.COUP:
                target_player = self.get_player_by_id(action.target_player_id)
                target_player_agent = self.agents[target_player.agent_id]
                target_player_agent.choose_card_to_reveal(target_player.hand)
                player.action_coup(target_player)
                last_actions.append(
                    f"{player.name} launched a Coup on {target_player.name}"
                )
        else:
            if action.can_be_challenged:
                last_actions.append(
                    f"Player {player.name} tries to use {action.action_type}"
                )
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
                    # Select a challenge
                    selected_challenge = random.choice(challenges)
                    challenging_player = self.get_player_by_id(
                        selected_challenge.origin_player_id
                    )
                    challenging_player_agent = self.agents[challenging_player.agent_id]
                    last_actions.append(
                        f"{challenging_player.name} is challenging {action.action_type} by {player.name}"
                    )
                    is_bluffing, action_card = player.is_bluffing(action)
                    # Challenge successful
                    if is_bluffing:
                        agent.choose_card_to_reveal(player.hand)
                        # Player still pays for failedassassin action
                        if action.action_type == ActionType.ASSASSIN:
                            player.lose_coins(3)
                        last_actions.append(
                            f"{player.name} was bluffing action {action.action_type} and lost an influence"
                        )
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
                        if (
                            action.action_type == ActionType.DUKE
                        ):  # TODO remaining cases
                            player.action_duke()
                            last_actions.append(
                                f"{player.name} gained 3 coins with duke"
                            )
                        elif action.action_type == ActionType.CAPTAIN:
                            target_player = self.get_player_by_id(
                                action.target_player_id
                            )
                            player.action_captain(target_player)
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
                            player.action_assassin(target_player)
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

            if action.can_be_countered:
                # Get eventual counters
                last_actions.append(
                    f"Player {player.name} tries to use {action.action_type}"
                )
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
                    # All challenges can be countered
                    challenge = agent.choose_challenge(
                        action_to_challenge=action,
                        player_to_challenge=countering_player,
                    )
                    # Player challenges countering player
                    if challenge.action_type == ActionType.CHALLENGE:
                        last_actions.append(
                            f"{player.name} is challenging {countering_player.name} with {challenge.action_type}"
                        )
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
                                player.action_foreign_aid()
                                last_actions.append(
                                    f"{player.name} successfully collected 2 coins with foreign aid"
                                )
                            elif action.action_type == ActionType.CAPTAIN:
                                target_player = self.get_player_by_id(
                                    action.target_player_id
                                )
                                player.action_captain(target_player)
                                last_actions.append(
                                    f"{player.name} successfully stole 2 coins from {target_player.name} with action {action.action_type}"
                                )
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
                    # Player does not challenge countering player
                    else:
                        last_actions.append(
                            f"{countering_player.name} successfully countered {action.action_type} from {player.name}"
                        )

                # Action is not countered
                else:
                    if action.action_type == ActionType.FOREIGN_AID:
                        player.action_foreign_aid()
                        last_actions.append(
                            f"{player.name} successfully collected 2 coins with foreign aid"
                        )
                    elif action.action_type == ActionType.CAPTAIN:
                        target_player = self.get_player_by_id(action.target_player_id)
                        player.action_captain(target_player)
                        last_actions.append(
                            f"{player.name} successfully stole 2 coins from {target_player.name} with action {action.action_type}"
                        )
                    elif action.action_type == ActionType.ASSASSIN:
                        target_player = self.get_player_by_id(action.target_player_id)
                        target_player_agent = self.agents[target_player.agent_id]
                        target_player_agent.choose_card_to_reveal(target_player.hand)
                        player.action_assassin(target_player)
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
        return last_actions

    def agents_next_move(self, last_actions: list[str], last_actions_max_length: int):
        if self.check_if_game_has_ended():
            return []

        # Get current player and their agent
        current_player = self.next_player
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
        self.update_states(last_actions)
        print(f"Last actions: {last_actions}")

        if self.check_if_game_has_ended():
            return []

        return last_actions
