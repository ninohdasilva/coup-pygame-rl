import sys
import pygame
from board import Board
from card import Card
from character import Character
from deck import Deck
from player import Player

pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
BOARD_TOP = 200
LAST_ACTIONS_MAX_LENGTH = 3

# Colors
COLORS = {
    "background": (40, 44, 52),  # Dark blue-gray
    "board": (53, 59, 69),  # Lighter blue-gray
    "text": (171, 178, 191),  # Light gray
    "accent": (97, 175, 239),  # Bright blue
    "button": (86, 95, 108),  # Medium gray
    "button_hover": (98, 109, 124),
    "next_player": (152, 195, 121),  # Green
    "dead_player": (224, 108, 117),  # Red
    "border": (86, 95, 108),  # Medium gray
}

# Initialize pygame
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Coup - AI Learning Simulation")
clock = pygame.time.Clock()

# Game settings
moves_per_second_options = [0.1, 0.2, 0.5, 1, 2, 5, 10]
moves_per_second = moves_per_second_options[0]
reveal_player_cards = False
is_active = False
last_actions = []
nb_games = 5
models_path = "models"

# Training metrics
plot_scores = []
plot_mean_scores = []
total_score = 0
record = 0
n_games = 0

# Board setup
board = Board()
board_zone_rect = pygame.Rect(0, BOARD_TOP, WINDOW_WIDTH, WINDOW_HEIGHT - BOARD_TOP)
card_width = 100  # Slightly larger cards
card_height = 100

# Training stats display
stats_font = pygame.font.Font(None, 24)


def display_training_stats(screen: pygame.Surface):
    stats_surface = pygame.Surface((200, 100))
    stats_surface.fill(COLORS["background"])
    stats_text = [
        f"Games: {n_games}",
        f"Record: {record:.1f}",
        f"Mean Score: {total_score / max(1, n_games):.1f}",
    ]
    for i, text in enumerate(stats_text):
        text_surface = stats_font.render(text, True, COLORS["text"])
        stats_surface.blit(text_surface, (10, i * 25))
    screen.blit(stats_surface, (10, BOARD_TOP + 10))


# Fonts
title_font = pygame.font.Font(None, 48)
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
last_actions_font = pygame.font.Font(None, 16)

# Button dimensions
BUTTON_WIDTH = 160
BUTTON_HEIGHT = 80
BUTTON_MARGIN = 20
# cards
face_down_card = pygame.image.load("assets/face_down_card.png").convert_alpha()
duke_card = pygame.image.load("assets/duke.png").convert_alpha()
assassin_card = pygame.image.load("assets/assassin.png").convert_alpha()
ambassador_card = pygame.image.load("assets/ambassador.png").convert_alpha()
captain_card = pygame.image.load("assets/captain.png").convert_alpha()
contessa_card = pygame.image.load("assets/contessa.png").convert_alpha()
# UI elements
reveal_cards_button_rect = pygame.Rect(
    BUTTON_MARGIN, BUTTON_MARGIN, BUTTON_WIDTH, BUTTON_HEIGHT
)
speed_button_rect = pygame.Rect(
    2 * BUTTON_MARGIN + BUTTON_WIDTH, BUTTON_MARGIN, BUTTON_WIDTH, BUTTON_HEIGHT
)
start_button_rect = pygame.Rect(
    3 * BUTTON_MARGIN + 2 * BUTTON_WIDTH, BUTTON_MARGIN, BUTTON_WIDTH, BUTTON_HEIGHT
)


def draw_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    is_active: bool = False,
    is_hover: bool = False,
):
    """Helper function to draw consistent buttons"""
    color = COLORS["button_hover"] if is_hover else COLORS["button"]
    if is_active:
        color = COLORS["accent"]

    # Draw button background with rounded corners
    pygame.draw.rect(screen, color, rect, border_radius=10)

    # Add a subtle 3D effect
    pygame.draw.rect(screen, COLORS["border"], rect, width=2, border_radius=10)

    # Center the text
    text_surface = font.render(text, True, COLORS["text"])
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)


def display_start_menu(screen: pygame.Surface):
    global is_active, last_actions

    # Draw title
    title = "COUP"
    subtitle = "AI Learning Simulation"

    # Create a gradient effect for the title
    base_color = COLORS["accent"]
    for i in range(5):
        # Ensure color values stay within valid RGB range (0-255)
        color = tuple(min(255, c + i * 10) for c in base_color)
        title_surface = title_font.render(title, True, color)
        title_rect = title_surface.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50 + i)
        )
        screen.blit(title_surface, title_rect)

    # Draw subtitle
    subtitle_surface = font.render(subtitle, True, COLORS["text"])
    subtitle_rect = subtitle_surface.get_rect(
        center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20)
    )
    screen.blit(subtitle_surface, subtitle_rect)

    # Draw start button with hover effect
    start_button = pygame.Rect(
        WINDOW_WIDTH // 2 - BUTTON_WIDTH // 2,
        WINDOW_HEIGHT // 2 + 80,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    mouse_pos = pygame.mouse.get_pos()
    is_hover = start_button.collidepoint(mouse_pos)

    draw_button(screen, start_button, "Start Game", False, is_hover)

    if is_hover and pygame.mouse.get_pressed()[0]:
        is_active = True
        board.start()


def display_game_over(screen: pygame.Surface):
    global last_actions, n_games
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Semi-transparent black
    screen.blit(overlay, (0, 0))

    # Get the winner (the only player with unrevealed cards)
    winner = next(p for p in board.players if p.is_alive)

    # Draw winner announcement
    text = f"{winner.name} Wins!"
    for i in range(3):  # Create a glowing effect
        text_surface = title_font.render(
            text, True, tuple(min(255, c + i * 20) for c in COLORS["next_player"])
        )
        text_rect = text_surface.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - i * 2)
        )
        screen.blit(text_surface, text_rect)

    # Draw restart button
    restart_button = pygame.Rect(
        WINDOW_WIDTH // 2 - BUTTON_WIDTH // 2,
        WINDOW_HEIGHT // 2 + 50,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )
    mouse_pos = pygame.mouse.get_pos()
    is_hover = restart_button.collidepoint(mouse_pos)
    draw_button(screen, restart_button, "New Game", False, is_hover)

    if is_hover and pygame.mouse.get_pressed()[0]:
        # Clear the screen before restarting
        screen.fill(COLORS["background"])
        pygame.display.update()
        # Reset game state
        last_actions = []
        board.start()

        # Update training metrics
        n_games += 1


def display_reveal_cards_button(
    screen: pygame.Surface, reveal_cards_button_rect: pygame.Rect
):
    mouse_pos = pygame.mouse.get_pos()
    is_hover = reveal_cards_button_rect.collidepoint(mouse_pos)
    draw_button(
        screen,
        reveal_cards_button_rect,
        "Hide Cards" if reveal_player_cards else "Show Cards",
        reveal_player_cards,
        is_hover,
    )


def display_ui_and_info(screen: pygame.Surface):
    # Draw top bar background
    ui_and_info_rect = pygame.Rect(0, 0, WINDOW_WIDTH, BOARD_TOP)
    pygame.draw.rect(screen, COLORS["board"], ui_and_info_rect)
    pygame.draw.line(
        screen, COLORS["border"], (0, BOARD_TOP), (WINDOW_WIDTH, BOARD_TOP), 2
    )

    # Draw buttons
    display_reveal_cards_button(screen, reveal_cards_button_rect)
    display_speed_button(screen, speed_button_rect)

    # Draw info panel
    info_rect = pygame.Rect(
        WINDOW_WIDTH - 400, BUTTON_MARGIN, 380, BOARD_TOP - 2 * BUTTON_MARGIN
    )
    display_info(screen, info_rect)


def display_info(screen: pygame.Surface, info_rect: pygame.Rect):
    # Draw info panel background with rounded corners
    pygame.draw.rect(screen, COLORS["background"], info_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS["border"], info_rect, width=2, border_radius=10)

    # Draw title
    title_surface = font.render("Last Actions", True, COLORS["accent"])
    title_rect = title_surface.get_rect(midtop=(info_rect.centerx, info_rect.top + 15))
    screen.blit(title_surface, title_rect)

    # Draw actions with alternating background
    for i, action in enumerate(last_actions):
        action_rect = pygame.Rect(
            info_rect.left + 15,
            title_rect.bottom + 15 + i * 35,
            info_rect.width - 30,
            30,
        )
        if i % 2 == 0:
            pygame.draw.rect(screen, COLORS["board"], action_rect, border_radius=5)

        text_surface = last_actions_font.render(action, True, COLORS["text"])
        text_rect = text_surface.get_rect(
            midleft=(action_rect.left + 10, action_rect.centery)
        )
        screen.blit(text_surface, text_rect)


def display_speed_button(screen: pygame.Surface, speed_button_rect: pygame.Rect):
    mouse_pos = pygame.mouse.get_pos()
    is_hover = speed_button_rect.collidepoint(mouse_pos)
    draw_button(
        screen, speed_button_rect, f"{moves_per_second} moves/s", False, is_hover
    )


def display_text(
    screen: pygame.Surface,
    text: str,
    x: int,
    y: int,
    font: pygame.font.Font,
    color=None,
):
    if color is None:
        color = COLORS["text"]
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)


def display_card(
    screen: pygame.Surface, card: Card, x: int, y: int, reveal_card=None, is_dead=False
):
    if reveal_card is None:
        reveal_card = reveal_player_cards

    # Get the appropriate card image
    if reveal_card or card.is_revealed:
        card_image = None
        match card.character:
            case Character.DUKE:
                card_image = duke_card
            case Character.ASSASSIN:
                card_image = assassin_card
            case Character.AMBASSADOR:
                card_image = ambassador_card
            case Character.CAPTAIN:
                card_image = captain_card
            case Character.CONTESSA:
                card_image = contessa_card
    else:
        card_image = face_down_card

    # Scale and display the card image
    scaled_image = pygame.transform.scale(card_image, (card_width, card_height))
    screen.blit(scaled_image, (x, y))


def display_player_info(
    screen: pygame.Surface, player: Player, x: int, y: int, is_next_player: bool
):
    # Draw player info background
    info_rect = pygame.Rect(x - 60, y - 30, 120, 60)
    pygame.draw.rect(screen, COLORS["background"], info_rect, border_radius=8)

    # Draw border with appropriate color
    border_color = COLORS["next_player"] if is_next_player else COLORS["border"]
    if not player.is_alive:
        border_color = COLORS["dead_player"]
    pygame.draw.rect(screen, border_color, info_rect, width=2, border_radius=8)

    # Display player name and coins
    name_color = COLORS["next_player"] if is_next_player else COLORS["text"]
    if not player.is_alive:
        name_color = COLORS["dead_player"]

    display_text(
        screen,
        player.name,
        info_rect.centerx,
        info_rect.centery - 12,
        small_font,
        name_color,
    )
    display_text(
        screen,
        f"{player.coins} coins",
        info_rect.centerx,
        info_rect.centery + 12,
        small_font,
    )


def display_player_zone(
    screen: pygame.Surface,
    player: Player,
    x: int,
    y: int,
    player_zone_width: int = 200,
    player_zone_height: int = 100,
    player_index: int = 0,
    is_next_player: bool = False,
):
    # Draw player zone background with a subtle gradient
    player_zone = pygame.Rect(x, y, player_zone_width, player_zone_height)

    # Create gradient effect
    gradient_surface = pygame.Surface(
        (player_zone_width, player_zone_height), pygame.SRCALPHA
    )
    color1 = COLORS["board"]
    color2 = tuple(max(0, c - 20) for c in color1)  # Slightly darker

    for i in range(player_zone_height):
        progress = i / player_zone_height
        current_color = tuple(
            int(c1 * (1 - progress) + c2 * progress) for c1, c2 in zip(color1, color2)
        )
        pygame.draw.line(
            gradient_surface, current_color, (0, i), (player_zone_width, i)
        )

    screen.blit(gradient_surface, player_zone)

    # Draw cards and info based on player position
    if player_index % 2 == 0:  # Top or bottom player
        card_spacing = (player_zone_width - 2 * card_width) / 3
        card_y = player_zone.y + (player_zone_height - card_height) / 2

        for i, card in enumerate(player.hand):
            card_x = player_zone.x + card_spacing + i * (card_width + card_spacing)
            display_card(
                screen,
                card,
                card_x,
                card_y,
                reveal_card=reveal_player_cards,
                is_dead=not player.is_alive,
            )

        info_y = player_zone.bottom + 30 if player_index == 0 else player_zone.top - 30
        display_player_info(screen, player, player_zone.centerx, info_y, is_next_player)
    else:  # Left or right player
        card_spacing = (player_zone_height - 2 * card_height) / 3
        card_x = player_zone.x + (player_zone_width - card_width) / 2

        for i, card in enumerate(player.hand):
            card_y = player_zone.y + card_spacing + i * (card_height + card_spacing)
            display_card(
                screen,
                card,
                card_x,
                card_y,
                reveal_card=reveal_player_cards,
                is_dead=not player.is_alive,
            )

        info_x = player_zone.right + 60 if player_index == 3 else player_zone.left - 60
        display_player_info(screen, player, info_x, player_zone.centery, is_next_player)


def display_deck(screen: pygame.Surface, deck: Deck, x: int, y: int):
    if len(deck.deck) > 0:
        # Only display the top card of the deck
        display_card(screen, deck.deck[-1], x, y, reveal_card=False)


def display_board_background(screen: pygame.Surface):
    pygame.draw.rect(screen, COLORS["board"], board_zone_rect)

    # Add a subtle pattern to the board
    pattern_size = 20
    for x in range(0, WINDOW_WIDTH, pattern_size):
        for y in range(BOARD_TOP, WINDOW_HEIGHT, pattern_size):
            if (x + y) % (pattern_size * 2) == 0:
                pattern_rect = pygame.Rect(x, y, pattern_size, pattern_size)
                pygame.draw.rect(
                    screen, tuple(max(0, c - 5) for c in COLORS["board"]), pattern_rect
                )


def display_board(board: Board):
    screen.fill((255, 255, 255), board_zone_rect)
    # Position deck in the center of the board zone
    display_deck(
        screen,
        board.deck,
        board_zone_rect.x + board_zone_rect.width / 2 - card_width / 2,
        board_zone_rect.y + board_zone_rect.height / 2 - card_height / 2,
    )

    for i, player in enumerate(board.players):
        player_zone_width = 200 if i % 2 == 0 else 100
        player_zone_height = 100 if i % 2 == 0 else 200
        if i == 0:  # Top player
            x = board_zone_rect.x + board_zone_rect.width / 2 - player_zone_width / 2
            y = board_zone_rect.y
        elif i == 1:  # Right player
            x = board_zone_rect.x + board_zone_rect.width - player_zone_width
            y = board_zone_rect.y + board_zone_rect.height / 2 - player_zone_height / 2
        elif i == 2:  # Bottom player
            x = board_zone_rect.x + board_zone_rect.width / 2 - player_zone_width / 2
            y = board_zone_rect.y + board_zone_rect.height - player_zone_height
        elif i == 3:  # Left player
            x = board_zone_rect.x
            y = board_zone_rect.y + board_zone_rect.height / 2 - player_zone_height / 2
        display_player_zone(
            screen,
            player,
            x,
            y,
            player_zone_width,
            player_zone_height,
            player_index=i,
            is_next_player=board.next_player == player,
        )


move_timer = pygame.USEREVENT + 2
pygame.time.set_timer(move_timer, int(1000 / moves_per_second))

running = True
while running:
    # Fill background with base color
    screen.fill(COLORS["background"])

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and is_active:
            mouse_pos = event.pos
            # Check button clicks
            if reveal_cards_button_rect.collidepoint(mouse_pos):
                reveal_player_cards = not reveal_player_cards
            elif speed_button_rect.collidepoint(mouse_pos):
                current_index = moves_per_second_options.index(moves_per_second)
                next_index = (current_index + 1) % len(moves_per_second_options)
                moves_per_second = moves_per_second_options[next_index]
                pygame.time.set_timer(move_timer, int(1000 / moves_per_second))

        # Running game logic
        elif event.type == move_timer and is_active and not board.game_has_ended:
            last_actions = board.agents_next_move(last_actions, LAST_ACTIONS_MAX_LENGTH)

    # Draw game state
    if not is_active:
        display_start_menu(screen)
    else:
        display_board_background(screen)

        # Draw game elements
        display_board(board)
        display_ui_and_info(screen)
        display_training_stats(screen)

        # Draw game over state if applicable
        if board.game_has_ended:
            display_game_over(screen)

    pygame.display.update()
    clock.tick(60)  # limits FPS to 60

pygame.quit()
sys.exit()
