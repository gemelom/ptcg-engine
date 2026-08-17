"""
Custom exceptions for the PTCG game engine.

This module provides a hierarchy of exceptions for better error handling
and more informative error messages throughout the game engine.
"""


class PTCGError(Exception):
    """Base exception for all PTCG-related errors."""


# ============================================================================
# Game State Exceptions
# ============================================================================


class GameError(PTCGError):
    """Base exception for game state errors."""


class GameTermination(GameError):
    """
    Raised when the game ends normally.

    This is not an error but a signal that the game has concluded.
    Common causes:
    - All prize cards taken
    - No Pokemon in play
    - Deck empty at draw
    """


class GameNotStartedError(GameError):
    """Raised when an action is attempted before the game starts."""


class InvalidTurnError(GameError):
    """Raised when an action is attempted on the wrong turn."""


# ============================================================================
# Action Exceptions
# ============================================================================


class ActionError(PTCGError):
    """Base exception for action-related errors."""


class InvalidActionError(ActionError):
    """Raised when an invalid action is attempted."""


class UnknownActionTypeError(ActionError):
    """Raised when an unknown action type is encountered."""


class ActionEncodingError(ActionError):
    """Raised when action encoding/decoding fails."""


class ActionDecodingError(ActionEncodingError):
    """Raised when action decoding from array fails."""


# ============================================================================
# Card Exceptions
# ============================================================================


class CardError(PTCGError):
    """Base exception for card-related errors."""


class CardNotFoundError(CardError):
    """Raised when a card cannot be found."""


class InvalidCardPositionError(CardError):
    """Raised when a card is in an invalid position."""


class CardPlayError(CardError):
    """Raised when a card cannot be played."""


# ============================================================================
# Deck Exceptions
# ============================================================================


class DeckError(PTCGError):
    """Base exception for deck construction and validation errors."""


class InvalidDeckError(DeckError):
    """Raised when a deck does not satisfy the configured construction rules."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


# ============================================================================
# Player Exceptions
# ============================================================================


class PlayerError(PTCGError):
    """Base exception for player-related errors."""


class InvalidPlayerError(PlayerError):
    """Raised when an invalid player is referenced."""


class PlayerActionError(PlayerError):
    """Raised when a player cannot perform an action."""


# ============================================================================
# State Exceptions
# ============================================================================


class StateError(PTCGError):
    """Base exception for state-related errors."""


class InvalidAreaError(StateError):
    """Raised when an invalid game area is referenced."""


class StateEncodingError(StateError):
    """Raised when state encoding fails."""


# ============================================================================
# Energy Exceptions
# ============================================================================


class EnergyError(PTCGError):
    """Base exception for energy-related errors."""


class InsufficientEnergyError(EnergyError):
    """Raised when there's not enough energy for an attack or retreat."""


class InvalidEnergyTypeError(EnergyError):
    """Raised when an invalid energy type is used."""


# ============================================================================
# Ability Exceptions
# ============================================================================


class AbilityError(PTCGError):
    """Base exception for ability-related errors."""


class AbilityNotAvailableError(AbilityError):
    """Raised when an ability cannot be used."""


class AbilityAlreadyUsedError(AbilityError):
    """Raised when a once-per-turn ability is used again."""
