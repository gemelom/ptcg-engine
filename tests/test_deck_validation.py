from __future__ import annotations

from random import Random

import pytest

from ptcg import PokemonTCG
from ptcg.core.deck import Deck
from ptcg.core.exceptions import InvalidDeckError
from ptcg.core.player import Player
from ptcg.utils.deck_validation import get_available_decks
from ptcg.utils.load_deck import load_deck
from tests.helpers.cards import make_card


def _cards(card_id: str, count: int):
    return [make_card(card_id) for _ in range(count)]


def test_bundled_decks_are_valid_for_standard_play():
    for deck_name in get_available_decks():
        assert load_deck(deck_name).is_valid(), deck_name


def test_standard_deck_requires_exactly_sixty_cards():
    deck = Deck(_cards("PAF-007", 4) + _cards("SVE-002", 55))

    assert deck.is_valid() is False
    with pytest.raises(InvalidDeckError, match="exactly 60 cards"):
        deck.validate()


def test_standard_deck_limits_same_name_across_printings_to_four():
    deck = Deck(_cards("PAF-007", 4) + _cards("OBF-026", 1) + _cards("SVE-002", 55))

    with pytest.raises(InvalidDeckError, match="Charmander.*5 copies"):
        deck.validate()


def test_standard_deck_allows_more_than_four_basic_energy():
    deck = Deck(_cards("PAF-007", 4) + _cards("SVE-002", 56))

    deck.validate()
    assert deck.is_valid() is True


def test_standard_deck_requires_a_basic_pokemon():
    deck = Deck(_cards("SVE-002", 60))

    with pytest.raises(InvalidDeckError, match="at least one Basic Pokemon"):
        deck.validate()


def test_environment_rejects_invalid_deck_before_starting(tmp_path):
    deck_path = tmp_path / "invalid.txt"
    deck_path.write_text("1 Charmander PAF 007\n", encoding="utf-8")
    env = PokemonTCG(deck1=str(deck_path), deck2=str(deck_path), record_game=False)

    with pytest.raises(InvalidDeckError, match="exactly 60 cards"):
        env.reset()


def test_player_shuffle_rejects_deck_without_basic_pokemon():
    player = Player(Deck(_cards("SVE-002", 60)))

    with pytest.raises(InvalidDeckError, match="at least one Basic Pokemon"):
        player.shuffle(Random(42))
