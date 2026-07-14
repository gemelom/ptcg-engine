import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardType, EnergyType
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("TEF-128")
@pytest.mark.card_coverage(
    "TEF-128",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_dunsparce_gnaw_damages_opponent():
    dunsparce = make_card("TEF-128")
    dunsparce.energy = [CardType.COLORLESS]
    defender = make_card("PAF-007")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[dunsparce],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    attacks = [a for a in dunsparce.get_actions(state) if isinstance(a, AttackAction)]
    gnaw = [a for a in attacks if a.attack.name == "Gnaw"]
    assert len(gnaw) == 1

    list(dunsparce.reduce_action(gnaw[0], state))

    assert defender.hp == 60  # 70 - 10
    assert state.turn == state.player2.id


def test_dunsparce_unavailable_without_energy():
    dunsparce = make_card("TEF-128")
    defender = make_card("PAF-007")
    state = make_state(PlayerZones(active=[dunsparce]), PlayerZones(active=[defender]))

    assert [a for a in dunsparce.get_actions(state) if isinstance(a, AttackAction)] == []


@pytest.mark.card("TEF-129")
@pytest.mark.card_coverage(
    "TEF-129",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_dudunsparce_run_away_draw_draws_three_and_shuffles_self_into_deck():
    dudunsparce = make_card("TEF-129")
    benched = make_card("PAF-007")
    deck_cards = [make_card("SVE-002"), make_card("SVE-004"), make_card("SVE-005")]
    state = make_state(
        PlayerZones(
            left=deck_cards,
            active=[dudunsparce],
            bench=[benched],
        )
    )
    state.player1.onceUsedTurn["Run Away Draw"] = False

    ability_actions = [a for a in dudunsparce.get_actions(state) if isinstance(a, UseAbilityAction)]
    assert len(ability_actions) == 1

    prompts = drive_choices(
        dudunsparce.reduce_action(ability_actions[0], state),
        [lambda _info: [benched]],  # choose bench replacement
    )

    assert len(state.player1.hand) == 3
    assert dudunsparce not in state.player1.active
    assert dudunsparce in state.player1.left
    assert state.player1.onceUsedTurn["Run Away Draw"] is True


def test_dudunsparce_run_away_draw_unavailable_after_use():
    dudunsparce = make_card("TEF-129")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], active=[dudunsparce], bench=[make_card("PAF-007")])
    )
    state.player1.onceUsedTurn["Run Away Draw"] = True

    assert [a for a in dudunsparce.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_dudunsparce_land_crush_damages_opponent():
    dudunsparce = make_card("TEF-129")
    dudunsparce.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[dudunsparce],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Run Away Draw"] = False

    attacks = [a for a in dudunsparce.get_actions(state) if isinstance(a, AttackAction)]
    assert len(attacks) == 1

    list(dudunsparce.reduce_action(attacks[0], state))

    assert defender.hp == 240  # 330 - 90
    assert state.turn == state.player2.id


@pytest.mark.card("TEF-137")
@pytest.mark.card_coverage(
    "TEF-137",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_cinccino_special_roll_does_70_per_special_energy():
    cinccino = make_card("TEF-137")
    cinccino.energy = [CardType.COLORLESS, CardType.COLORLESS]
    special1 = make_card("BRS-151")  # Double Turbo Energy - special
    special2 = make_card("SIT-169")  # V Guard Energy - special
    cinccino.attachment = [special1, special2]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[cinccino],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    attacks = [a for a in cinccino.get_actions(state) if isinstance(a, AttackAction) and a.attack.name == "Special Roll"]
    assert len(attacks) == 1

    list(cinccino.reduce_action(attacks[0], state))

    assert defender.hp == 190  # 330 - 140 (2 * 70)


def test_cinccino_gentle_slap_damages_opponent():
    cinccino = make_card("TEF-137")
    cinccino.energy = [CardType.COLORLESS]
    defender = make_card("PAF-007")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[cinccino],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    attacks = [a for a in cinccino.get_actions(state) if isinstance(a, AttackAction) and a.attack.name == "Gentle Slap"]
    assert len(attacks) == 1

    list(cinccino.reduce_action(attacks[0], state))

    assert defender.hp == 40  # 70 - 30
