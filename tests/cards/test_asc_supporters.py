import pytest

from ptcg.core.action import UseSupporterAction
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("ASC-192")
@pytest.mark.card_coverage(
    "ASC-192",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
)
def test_lillies_determination_shuffles_hand_and_draws_eight_with_six_prizes(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    lillies_determination = make_card("ASC-192")
    fire_energy = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    drawn_cards = [
        make_card("SVE-002"),
        make_card("SVE-004"),
        make_card("SVE-005"),
        make_card("SVE-007"),
        make_card("SVE-008"),
        make_card("PAF-007"),
        make_card("PAF-008"),
        make_card("PAF-027"),
    ]
    extra_deck_card = make_card("PAF-084")
    state = make_state(
        PlayerZones(
            hand=[lillies_determination, fire_energy, lightning_energy],
            left=drawn_cards + [extra_deck_card],
            prize=[make_card("PAF-007") for _ in range(6)],
        )
    )

    actions = lillies_determination.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseSupporterAction)

    lillies_determination.reduce_action(actions[0], state)

    assert lillies_determination in state.player1.discard
    assert len(state.player1.hand) == 8
    assert set(state.player1.hand) == set(drawn_cards)
    assert fire_energy in state.player1.left
    assert lightning_energy in state.player1.left
    assert extra_deck_card in state.player1.left
    assert state.player1.supporterPlayedTurn is True


def test_lillies_determination_draws_six_when_prizes_are_not_six(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    lillies_determination = make_card("ASC-192")
    drawn_cards = [
        make_card("SVE-002"),
        make_card("SVE-004"),
        make_card("SVE-005"),
        make_card("SVE-007"),
        make_card("SVE-008"),
        make_card("PAF-007"),
    ]
    remaining_card = make_card("PAF-008")
    state = make_state(
        PlayerZones(
            hand=[lillies_determination],
            left=drawn_cards + [remaining_card],
            prize=[make_card("PAF-007") for _ in range(5)],
        )
    )

    lillies_determination.reduce_action(lillies_determination.get_actions(state)[0], state)

    assert len(state.player1.hand) == 6
    assert set(state.player1.hand) == set(drawn_cards)
    assert remaining_card in state.player1.left


def test_lillies_determination_is_unavailable_after_supporter_played():
    lillies_determination = make_card("ASC-192")
    state = make_state(PlayerZones(hand=[lillies_determination]))
    state.player1.supporterPlayedTurn = True

    assert lillies_determination.get_actions(state) == []
