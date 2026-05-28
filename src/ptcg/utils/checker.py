from dataclasses import dataclass
from typing import List, Sequence

from ptcg.core.card import Card, EnergyCard, PokemonCard
from ptcg.core.enums import CardPosition, PokemonPosition
from ptcg.core.player import Player
from ptcg.core.state import State


class StateCheckError(Exception):
    """Raised when state validation fails."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


@dataclass
class ZoneConfig:
    """Configuration for a player zone."""

    attr_name: str
    position: CardPosition
    max_size: int | None = None
    exact_size: int | None = None


class StateChecker:
    """State validation checker with unified error handling.

    Usage:
        checker = StateChecker(state)
        checker.check()  # Raises StateCheckError if invalid
    """

    POKEMON_ZONES: List[ZoneConfig] = [
        ZoneConfig("active", CardPosition.ACTIVE, exact_size=1),
        ZoneConfig("bench", CardPosition.BENCH, max_size=5),
    ]

    CARD_ZONES: List[ZoneConfig] = [
        ZoneConfig("hand", CardPosition.HAND),
        ZoneConfig("left", CardPosition.LEFT),
        ZoneConfig("discard", CardPosition.DISCARD),
        ZoneConfig("prize", CardPosition.PRIZE),
    ]

    def __init__(self):
        self.errors: List[str] = []

    def check(self, state) -> None:
        """Run all checks. Raises StateCheckError if any validation fails."""
        self.state = state
        self.errors = []

        for player in [state.player1, state.player2]:
            self._check_player(state, player)

        if self.errors:
            raise StateCheckError(self.errors)

    def _check_player(self, state: State, player: Player) -> None:
        """Run all checks for a single player."""
        self._check_pokemon_positions(state, player)
        self._check_zone_sizes(state, player)
        self._check_energy_consistency(state, player)
        self._check_card_indices(state, player)

    def _check_pokemon_positions(self, state: State, player: Player) -> None:
        """Verify Pokemon position attributes match their zone."""
        for zone_config in self.POKEMON_ZONES:
            zone: Sequence[PokemonCard] = getattr(player, zone_config.attr_name)
            expected_pos = (
                PokemonPosition.ACTIVE
                if zone_config.attr_name == "active"
                else PokemonPosition.BENCH
            )

            for pokemon in zone:
                if pokemon.position != expected_pos:
                    self._add_error(
                        state,
                        f"[{player.id}] {pokemon} in {zone_config.attr_name} has "
                        f"position={pokemon.position}, expected={expected_pos}",
                    )

    def _check_zone_sizes(self, state: State, player: Player) -> None:
        """Verify zone sizes are within limits."""
        for zone_config in self.POKEMON_ZONES + self.CARD_ZONES:
            zone = getattr(player, zone_config.attr_name)
            size = len(zone)

            if zone_config.exact_size is not None and size != zone_config.exact_size:
                self._add_error(
                    state,
                    f"[{player.id}] {zone_config.attr_name} size={size}, "
                    f"expected exact={zone_config.exact_size}",
                )
            elif zone_config.max_size is not None and size > zone_config.max_size:
                self._add_error(
                    state,
                    f"[{player.id}] {zone_config.attr_name} size={size}, "
                    f"max allowed={zone_config.max_size}",
                )

    def _check_energy_consistency(self, state: State, player: Player) -> None:
        """Verify pokemon.energy matches attachment energy cards."""
        for pokemon in player.active + player.bench:
            attached_energy = []
            for card in pokemon.attachment:
                if isinstance(card, EnergyCard):
                    attached_energy.extend(card.provides)

            expected = sorted(attached_energy, key=lambda e: e.value)
            actual = sorted(pokemon.energy, key=lambda e: e.value)

            if expected != actual:
                self._add_error(
                    state,
                    f"[{player.id}] {pokemon.__class__.__name__} energy mismatch: "
                    f"attachment provides {expected}, but energy={actual}",
                )

    def _check_card_indices(self, state: State, player: Player) -> None:
        """Verify card indices and positions are correct."""
        for zone_config in self.POKEMON_ZONES + self.CARD_ZONES:
            zone: Sequence[Card] = getattr(player, zone_config.attr_name)

            for idx, card in enumerate(zone):
                expected_idx = idx + 1

                if card.cardPosition != zone_config.position:
                    self._add_error(
                        state,
                        f"[{player.id}] {card} in {zone_config.attr_name} has "
                        f"cardPosition={card.cardPosition}, expected={zone_config.position}",
                    )

                if card.index != expected_idx:
                    self._add_error(
                        state,
                        f"[{player.id}] {card} in {zone_config.attr_name}[{idx}] has "
                        f"index={card.index}, expected={expected_idx}",
                    )

    def _add_error(self, state: State, message: str) -> None:
        """Add an error with context information."""
        context = f"turn={state.turn}, timestep={state.timestep}"
        self.errors.append(f"[{context}] {message}")
