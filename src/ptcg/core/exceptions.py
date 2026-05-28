"""
Custom exceptions for the PTCG game engine.

This module provides a hierarchy of exceptions for better error handling
and more informative error messages throughout the game engine.
"""


class PTCGError(Exception):
    """Base exception for all PTCG-related errors."""

    pass


# ============================================================================
# Game State Exceptions
# ============================================================================


class GameError(PTCGError):
    """Base exception for game state errors."""

    pass


class GameTermination(GameError):
    """
    Raised when the game ends normally.

    This is not an error but a signal that the game has concluded.
    Common causes:
    - All prize cards taken
    - No Pokemon in play
    - Deck empty at draw
    """

    pass


class GameNotStartedError(GameError):
    """Raised when an action is attempted before the game starts."""

    pass


class InvalidTurnError(GameError):
    """Raised when an action is attempted on the wrong turn."""

    pass


# ============================================================================
# Action Exceptions
# ============================================================================


class ActionError(PTCGError):
    """Base exception for action-related errors."""

    pass


class InvalidActionError(ActionError):
    """Raised when an invalid action is attempted."""

    pass


class UnknownActionTypeError(ActionError):
    """Raised when an unknown action type is encountered."""

    pass


class ActionEncodingError(ActionError):
    """Raised when action encoding/decoding fails."""

    pass


class ActionDecodingError(ActionEncodingError):
    """Raised when action decoding from array fails."""

    pass


# ============================================================================
# Card Exceptions
# ============================================================================


class CardError(PTCGError):
    """Base exception for card-related errors."""

    pass


class CardNotFoundError(CardError):
    """Raised when a card cannot be found."""

    pass


class InvalidCardPositionError(CardError):
    """Raised when a card is in an invalid position."""

    pass


class CardPlayError(CardError):
    """Raised when a card cannot be played."""

    pass


# ============================================================================
# Player Exceptions
# ============================================================================


class PlayerError(PTCGError):
    """Base exception for player-related errors."""

    pass


class InvalidPlayerError(PlayerError):
    """Raised when an invalid player is referenced."""

    pass


class PlayerActionError(PlayerError):
    """Raised when a player cannot perform an action."""

    pass


# ============================================================================
# State Exceptions
# ============================================================================


class StateError(PTCGError):
    """Base exception for state-related errors."""

    pass


class InvalidAreaError(StateError):
    """Raised when an invalid game area is referenced."""

    pass


class StateEncodingError(StateError):
    """Raised when state encoding fails."""

    pass


# ============================================================================
# Energy Exceptions
# ============================================================================


class EnergyError(PTCGError):
    """Base exception for energy-related errors."""

    pass


class InsufficientEnergyError(EnergyError):
    """Raised when there's not enough energy for an attack or retreat."""

    pass


class InvalidEnergyTypeError(EnergyError):
    """Raised when an invalid energy type is used."""

    pass


# ============================================================================
# Ability Exceptions
# ============================================================================


class AbilityError(PTCGError):
    """Base exception for ability-related errors."""

    pass


class AbilityNotAvailableError(AbilityError):
    """Raised when an ability cannot be used."""

    pass


class AbilityAlreadyUsedError(AbilityError):
    """Raised when a once-per-turn ability is used again."""

    pass
