import pytest

from ptcg.core.action import DiscardStadiumAction, PutStadiumAction, UseStadiumAction
from ptcg.core.enums import CardPosition, PlayerId, PokemonPosition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAL-171")
@pytest.mark.card_coverage(
    "PAL-171",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_artazon_moves_from_hand_to_stadium():
    artazon = make_card("PAL-171")
    state = make_state(PlayerZones(hand=[artazon]))

    actions = artazon.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], PutStadiumAction)

    list(artazon.reduce_action(actions[0], state))

    assert state.stadium == [artazon]
    assert artazon not in state.player1.hand
    assert artazon.cardPosition == CardPosition.STADIUM
    assert artazon.playedFrom == PlayerId.PLAYER1
    assert state.player1.stadiumPlayedTurn is True


def test_artazon_puts_basic_no_rule_box_pokemon_from_deck_onto_bench(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    artazon = make_card("PAL-171")
    charmander = make_card("PAF-007")
    charizard_ex = make_card("PAF-054")
    rare_candy = make_card("PAF-089")
    state = make_state(PlayerZones(left=[rare_candy, charmander, charizard_ex]))
    state.stadium = [artazon]

    actions = artazon.get_actions(state)
    use_actions = [action for action in actions if isinstance(action, UseStadiumAction)]
    assert len(use_actions) == 1

    prompts = drive_choices(
        artazon.reduce_action(use_actions[0], state),
        [lambda _info: [charmander]],
    )

    assert prompts[0]["prompt"].source is artazon
    assert prompts[0]["prompt"].candidates == [charmander]
    assert state.player1.bench == [charmander]
    assert charmander.cardPosition == CardPosition.BENCH
    assert charmander.position == PokemonPosition.BENCH
    assert state.player1.left == [rare_candy, charizard_ex]
    assert state.player1.stadiumUsedTurn is True


def test_artazon_search_is_unavailable_without_bench_space():
    artazon = make_card("PAL-171")
    bench = [make_card("PAF-007") for _ in range(5)]
    state = make_state(PlayerZones(left=[make_card("PAF-007")], bench=bench))
    state.stadium = [artazon]

    assert [
        action for action in artazon.get_actions(state) if isinstance(action, UseStadiumAction)
    ] == []


def test_artazon_search_is_unavailable_without_basic_no_rule_box_pokemon():
    artazon = make_card("PAL-171")
    state = make_state(PlayerZones(left=[make_card("PAF-054"), make_card("PAF-089")]))
    state.stadium = [artazon]

    assert [
        action for action in artazon.get_actions(state) if isinstance(action, UseStadiumAction)
    ] == []


def test_artazon_is_unavailable_after_stadium_played_this_turn():
    artazon = make_card("PAL-171")
    state = make_state(PlayerZones(hand=[artazon]))
    state.player1.stadiumPlayedTurn = True

    assert artazon.get_actions(state) == []


def test_artazon_discards_to_player_who_played_it():
    artazon = make_card("PAL-171")
    artazon.playedFrom = PlayerId.PLAYER2
    state = make_state()
    state.stadium = [artazon]

    list(artazon.reduce_action(DiscardStadiumAction(PlayerId.PLAYER1, artazon), state))

    assert state.stadium == []
    assert state.player1.discard == []
    assert [card.name for card in state.player2.discard] == ["Artazon"]
