# Coup - AI Learning Simulation

A Python implementation of the board game "Coup" using Pygame, with AI agents learning through reinforcement learning. This project simulates the game mechanics and provides a visual interface to watch AI agents play and learn the game strategies.

![Coup Game Screenshot](assets/screenshot.png)

## Features

- Full implementation of Coup game mechanics
- Visual game interface using Pygame
- AI agents using reinforcement learning
- Real-time visualization of game state
- Adjustable simulation speed
- Training statistics display
- Card reveal functionality for debugging

## Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

## Running the Simulation

To start the simulation:

```bash
uv run src/simulation.py
```

## Game Controls

- **Show/Hide Cards**: Toggle to reveal or hide all player cards
- **Speed Control**: Adjust the simulation speed (0.1 to 10 moves per second)
- **Start Game**: Begin a new game simulation
- **New Game**: Start a fresh game after one ends

## Project Structure

```
coup-pygame-rl/
├── assets/           # Game assets (card images)
├── src/             
│   ├── agent.py     # AI agent implementation
│   ├── board.py     # Game board logic
│   ├── card.py      # Card class implementation
│   ├── character.py # Character types
│   ├── deck.py      # Deck management
│   ├── player.py    # Player class implementation
│   └── simulation.py # Main game loop and visualization
├── pyproject.toml   # Project dependencies
└── README.md
```

## Dependencies

- pygame (2.6.1+): Game engine and visualization
- numpy (2.3.2+): Numerical computations
- torch (2.8.0+): Machine learning framework
- pydantic (2.11.7+): Data validation

## Credits

- Card assets from [KenneyNL](http://kenney.nl/)