import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardType, PlayerId
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PRE-043")
@pytest.mark.card_coverage(
    "PRE-043",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_flutter_mane_hex_hurl_damages_active_and_places_two_bench_damage_counters():
    flutter_mane = make_card("PRE-043")
    flutter_mane.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    benched_target = make_card("PAF-007")
    other_bench = make_card("PAF-027")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[flutter_mane],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
            bench=[benched_target, other_bench],
        ),
    )

    hex_hurl = [
        action
        for action in flutter_mane.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Hex Hurl"
    ]
    assert len(hex_hurl) == 1

    prompts = drive_choices(
        flutter_mane.reduce_action(hex_hurl[0], state),
        [
            lambda _info: [benched_target],
            lambda _info: [benched_target],
        ],
    )

    assert prompts[0]["prompt"].source is flutter_mane
    assert prompts[0]["prompt"].candidates == [benched_target, other_bench]
    assert prompts[1]["prompt"].source is flutter_mane
    assert prompts[1]["prompt"].candidates == [benched_target, other_bench]
    assert defender.hp == 240
    assert benched_target.hp == 50
    assert other_bench.hp == 70
    assert state.turn == state.player2.id


def test_flutter_mane_hex_hurl_unavailable_without_energy():
    flutter_mane = make_card("PRE-043")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[flutter_mane]), PlayerZones(active=[defender]))

    assert [
        action for action in flutter_mane.get_actions(state) if isinstance(action, AttackAction)
    ] == []


def test_flutter_mane_midnight_fluttering_suppresses_opponents_active_abilities():
    flutter_mane = make_card("PRE-043")
    rotom = make_card("CRZ-045")
    state = make_state(
        PlayerZones(active=[flutter_mane]),
        PlayerZones(active=[rotom]),
        turn=PlayerId.PLAYER2,
    )

    assert [action for action in rotom.get_actions(state) if isinstance(action, UseAbilityAction)]
    assert [
        action
        for action in state.player2.get_actions(state)
        if isinstance(action, UseAbilityAction)
    ] == []
