from __future__ import annotations

from dataclasses import dataclass, field

from ptcg.core.card import Card, PokemonCard
from ptcg.core.deck import Deck
from ptcg.core.enums import CardPosition, PlayerId, PokemonPosition
from ptcg.core.player import Player
from ptcg.core.state import State


@dataclass
class PlayerZones:
    hand: list[Card] = field(default_factory=list)
    left: list[Card] = field(default_factory=list)
    discard: list[Card] = field(default_factory=list)
    prize: list[Card] = field(default_factory=list)
    active: list[PokemonCard] = field(default_factory=list)
    bench: list[PokemonCard] = field(default_factory=list)


def make_state(
    player1: PlayerZones | None = None,
    player2: PlayerZones | None = None,
    turn: PlayerId = PlayerId.PLAYER1,
) -> State:
    p1 = _make_player(PlayerId.PLAYER1, player1 or PlayerZones())
    p2 = _make_player(PlayerId.PLAYER2, player2 or PlayerZones())
    return State(player1=p1, player2=p2, turn=turn)


def _make_player(player_id: PlayerId, zones: PlayerZones) -> Player:
    player = Player(Deck([]))
    player.id = player_id
    player.hand = list(zones.hand)
    player.left = list(zones.left)
    player.discard = list(zones.discard)
    player.prize = list(zones.prize)
    player.active = list(zones.active)
    player.bench = list(zones.bench)
    player.supporterPlayedTurn = False

    _set_positions(player.hand, CardPosition.HAND)
    _set_positions(player.left, CardPosition.LEFT)
    _set_positions(player.discard, CardPosition.DISCARD)
    _set_positions(player.prize, CardPosition.PRIZE)
    _set_pokemon_positions(player.active, CardPosition.ACTIVE, PokemonPosition.ACTIVE)
    _set_pokemon_positions(player.bench, CardPosition.BENCH, PokemonPosition.BENCH)
    return player


def _set_positions(cards: list[Card], position: CardPosition) -> None:
    for index, card in enumerate(cards, start=1):
        card.cardPosition = position
        card.index = index


def _set_pokemon_positions(
    cards: list[PokemonCard],
    card_position: CardPosition,
    pokemon_position: PokemonPosition,
) -> None:
    for index, card in enumerate(cards, start=1):
        card.cardPosition = card_position
        card.position = pokemon_position
        card.index = index
