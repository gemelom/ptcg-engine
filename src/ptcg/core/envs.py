"""
Pokemon TCG Game Environment Module.

This module implements the main game environment using a generator-based
coroutine pattern for handling multi-step player interactions.

Generator Pattern Overview:
===========================
The environment uses Python generators to implement a cooperative multitasking
pattern where the game can pause at any point requiring player input.

Flow:
    env.reset()           → Creates generator, yields initial observation
    env.step(action)      → Sends action to generator, receives next state
    ...                   → Repeat until done

Generator Stack:
    step_async()          - Main game loop generator
      └─ reduce_action()  - Delegates to action source
           └─ card.reduce_action() / player.reduce_action()
                └─ reduce_choose_card_actions() - Card selection prompts

Key Concepts:
    - yield (obs, reward, done, info): Pause and return state to caller
    - send(action): Resume generator with player's choice
    - yield from: Delegate to sub-generator (e.g., card selection)
"""

import inspect
import random
from pathlib import Path
from typing import Generator, Optional

from loguru import logger

from ptcg.core.action import Action, PlayPokemonAction
from ptcg.core.enums import Coin, PlayerId, PokemonPosition, Stage, SuperType
from ptcg.core.exceptions import GameTermination
from ptcg.core.player import Player
from ptcg.core.recorder import GameRecorder
from ptcg.core.reducer import (
    choose_card_actions,
    reduce_choose_card_actions,
    reduce_play_pokemon_action,
)
from ptcg.core.state import State
from ptcg.utils.checker import StateChecker
from ptcg.utils.load_deck import load_deck
from ptcg.utils.utils import (
    current_player,
    flip_coin,
    judge_termination,
)

DEFAULT_DECK = "charizard_ex"
# DEFAULT_DECK = "gholdengo_ex"


class PokemonTCG:
    """Pokemon TCG game environment.

    This is a pure game engine that handles game state and actions.
    Agents/players are external to this class - the environment just
    provides observations and accepts actions.

    The environment follows a Gymnasium-like API with generator-based
    internal state management for handling multi-step interactions.

    Usage:
        env = PokemonTCG(seed=42)
        obs, reward, done, info = env.reset()

        while not done:
            action = agent.select_action(info["raw_available_actions"])
            obs, reward, done, info = env.step(action)

    Attributes:
        gamestate: Current game state container.
        logger: Game event logger.
        winner: Winner of the game (set when game ends).
        cur_available_actions: List of valid actions for current state.
    """

    gamestate: State
    recorder: GameRecorder
    winner: Optional[PlayerId]
    cur_available_actions: list[Action]
    reducer: Generator

    def __init__(
        self,
        seed: int = 0,
        render_mode: Optional[str] = None,
        verbose: bool = False,
        deck1: Optional[str] = None,
        deck2: Optional[str] = None,
        record_game: bool = True,
    ):
        self.seed = seed
        self.render_mode = render_mode
        self.deck1 = deck1
        self.deck2 = deck2
        self.verbose = verbose
        self.record_game = record_game
        self.state_checker = StateChecker()

        if verbose:
            logger.remove()
            logger.add(
                "ptcg_debug.log",
                rotation="10 MB",
                level="DEBUG",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            )

    # =========================================================================
    # Initialization & Reset
    # =========================================================================

    def reset(self, options: Optional[dict] = None) -> tuple:
        """Reset the game environment to initial state.

        This method:
        1. Loads decks for both players
        2. Creates and initializes game state
        3. Runs the start stage (choosing active Pokémon)
        4. Returns initial observation

        Args:
            options: Optional configuration (currently unused).

        Returns:
            Tuple of (observation, reward, done, info).
        """
        self._load_decks()
        self._init_game_state()
        self._init_generator()

        return self.reducer.send(None)

    def _load_decks(self) -> None:
        """Load decks for both players from files."""
        cur_dir = Path(__file__).parent
        default_deck_path = str(cur_dir / ".." / "decks" / f"{DEFAULT_DECK}.txt")

        self._deck1_cards = load_deck(self.deck1) if self.deck1 else load_deck(default_deck_path)
        self._deck2_cards = load_deck(self.deck2) if self.deck2 else load_deck(default_deck_path)

    def _init_game_state(self) -> None:
        player1 = Player(self._deck1_cards)
        player2 = Player(self._deck2_cards)

        self.gamestate = State(player1, player2)
        self.winner = None
        self.cur_available_actions = []

        if self.record_game:
            self.recorder = GameRecorder(self.seed)
        else:
            self.recorder = None  # type: ignore

        self.gamestate.player1.id = PlayerId.PLAYER1
        self.gamestate.player2.id = PlayerId.PLAYER2
        self.gamestate.player1.shuffle()
        self.gamestate.player2.shuffle()

        self.start_stage = True

    def _init_generator(self) -> None:
        """Initialize the main game loop generator."""
        self.reducer = self._game_loop()

    def get_players(self) -> tuple[Player, Player]:
        return self.gamestate.player1, self.gamestate.player2

    def get_actions(self, state: State) -> list[Action]:
        """Get valid actions for the current player.

        Args:
            state: Current game state.

        Returns:
            List of valid Action objects.
        """
        player = current_player(state)
        return player.get_actions(self.gamestate)

    # =========================================================================
    # Game Loop (Generator-based)
    # =========================================================================

    def _game_loop(self) -> Generator:
        """Main game loop generator.

        This generator implements the core game flow using Python's
        generator protocol for handling multi-step player interactions.

        Generator Protocol:
            - yield (obs, reward, done, info): Pause, return state, wait for action
            - send(action): Resume with player's chosen action

        Yields:
            Tuple of (observation, reward, done, info).
        """
        # Complete the start stage (initial Pokemon selection)
        yield from self._run_start_stage()

        # Yield the initial game state after start stage is complete
        action = yield self._yield_initial_state()

        while True:
            action = self._validate_action(action)
            self._log_action(action)

            yield from self._execute_action(action)

            obs, reward, done, info = self._prepare_step_result()

            if done:
                self._handle_game_end(info)
            else:
                self.state_checker.check(self.gamestate)

            action = yield (obs, reward, done, info)

    def _run_start_stage(self) -> Generator:
        """Run the game start stage where players choose active Pokémon.

        This handles the initial setup where each player selects their active Pokémon.
        The main loop will yield the initial game state after this completes.

        Yields:
            Observations during card selection for both players.
        """
        for player in [self.gamestate.player1, self.gamestate.player2]:
            self.gamestate.turn = player.id

            basic_pokemon = [
                card
                for card in player.hand
                if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
            ]

            actions = choose_card_actions(
                player.id,
                player.id,
                1,
                1,
                basic_pokemon,
                tips="The game start. You should choose 1 basic Pokemon and put it onto active spot.",
            )
            pokemon = yield from reduce_choose_card_actions(actions, self.gamestate)
            reduce_play_pokemon_action(
                PlayPokemonAction(player.id, pokemon[0], PokemonPosition.ACTIVE), self.gamestate
            )

        self.start_stage = False
        self._determine_first_player()
        self._log_game_start()

        # Don't return anything - let the main loop yield the initial state

    def _determine_first_player(self) -> None:
        """Determine which player goes first via coin flip."""
        if flip_coin(self.gamestate) == Coin.HEAD:
            self.gamestate.turn = PlayerId.PLAYER1
            self.gamestate.player2.supporterPlayedTurn = False
        else:
            self.gamestate.turn = PlayerId.PLAYER2
            self.gamestate.player1.supporterPlayedTurn = False

    def _log_game_start(self) -> None:
        player_name = f"{self.gamestate.turn}"[9:]
        if self.recorder:
            self.recorder.record_game_start(player_name, self.gamestate)

    def _yield_initial_state(self) -> tuple:
        """Create and return the initial game state tuple."""
        actions = self.get_actions(self.gamestate)
        self.cur_available_actions = actions

        return (
            self.gamestate.get_obs(),
            0,
            False,
            {
                "is_choosing_card": self.gamestate.is_choosing_card,
                "raw_available_actions": actions,
                "turn": self.gamestate.turn,
                "full_state": self.gamestate,
                "auto_executed": list(self.gamestate.auto_events),
            },
        )

    def _validate_action(self, action: Action) -> Action:
        if action in self.cur_available_actions:
            return action

        logger.debug(f"{self.gamestate.turn} invalid action: {action}")
        return random.choice(self.cur_available_actions)

    def _log_action(self, action: Action) -> None:
        if self.recorder:
            self.recorder.record_action(action)
        self.gamestate.actions_buffer.append(action)

    def _execute_action(self, action: Action) -> Generator:
        """Execute an action and handle any sub-interactions.

        This method delegates to the action's source (card/player) which
        may yield multiple times for multi-step actions.

        Args:
            action: The action to execute.

        Yields:
            (obs, reward, done, info) tuples for sub-interactions.
        """
        cur_player = current_player(self.gamestate)

        try:
            reducer = self._reduce_action()
            reducer.send(None)
            infos = reducer.send(action)

            while infos is not None:
                action = yield infos
                infos = reducer.send(action)

        except GameTermination:
            pass
        except StopIteration:
            pass

        cur_player.reward.calculate_step_reward()
        if self.gamestate.end_turn:
            self.gamestate.end_turn = False

        self.gamestate.timestep += 1
        if self.recorder:
            self.recorder.record_state(self.gamestate)

    def _reduce_action(self) -> Generator:
        """Generator that delegates action reduction to the source.

        The source (card or player) handles the actual state changes.
        This generator wraps the source's reduce_action for uniform handling.

        Yields:
            Whatever the source's reduce_action yields.
        """
        action = yield
        source = action.source

        acting_player = current_player(self.gamestate)
        if hasattr(action, "playerId") and action.playerId == acting_player.id:
            if not isinstance(source, type(acting_player)):
                acting_player.record_action(action)

        if inspect.isgeneratorfunction(source.reduce_action):
            yield from source.reduce_action(action, self.gamestate)
        else:
            source.reduce_action(action, self.gamestate)

    def _prepare_step_result(self) -> tuple:
        """Prepare the step result tuple.

        Returns:
            Tuple of (observation, reward, done, info).
        """
        cur_player = current_player(self.gamestate)
        obs = self.gamestate.get_obs()
        done, winner = judge_termination(self.gamestate)
        actions = self.get_actions(self.gamestate)
        reward = cur_player.reward.calculate_step_reward()

        self.cur_available_actions = actions

        info = {
            "is_choosing_card": self.gamestate.is_choosing_card,
            "raw_available_actions": actions,
            "turn": self.gamestate.turn,
            "full_state": self.gamestate,
            "auto_executed": list(self.gamestate.auto_events),
        }
        self.gamestate.auto_events = []

        if self.gamestate.turn_just_switched:
            info["opponent_last_turn_actions"] = self.gamestate.last_turn_opponent_actions
            self.gamestate.turn_just_switched = False

        if done:
            self.winner = winner
            info["winner"] = winner

        return obs, reward, done, info

    def _handle_game_end(self, info: dict) -> None:
        if self.recorder:
            self.recorder.record_termination(self.winner)

    # =========================================================================
    # Public API
    # =========================================================================

    def step(self, action: Action) -> tuple:
        """Execute one step in the environment.

        Args:
            action: The action to execute.

        Returns:
            Tuple of (observation, reward, done, info).
        """
        current_player(self.gamestate).reward.clear()

        try:
            return self.reducer.send(action)
        except StopIteration:
            # Generator exhausted, create new one for next turn
            self.reducer = self._game_loop()
            self.reducer.send(None)
            return self.reducer.send(action)

    def set_seed(self, seed: int) -> None:
        """Set random seed for reproducibility.

        Args:
            seed: The seed value.
        """
        self.seed = seed
        random.seed(seed)
