import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("TWM-128")
@pytest.mark.card_coverage(
    "TWM-128",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_dreepy_petty_grudge_damages_opponent():
    dreepy = make_card("TWM-128")
    dreepy.energy = [CardType.PSYCHIC]
    defender = make_card("PAF-007")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], prize=[make_card("SVE-004")], active=[dreepy]),
        PlayerZones(left=[make_card("SVE-005")], prize=[make_card("SVE-007")], active=[defender]),
    )

    attacks = [a for a in dreepy.get_actions(state) if isinstance(a, AttackAction) and a.attack.name == "Petty Grudge"]
    assert len(attacks) == 1

    list(dreepy.reduce_action(attacks[0], state))

    assert defender.hp == 60  # 70 - 10
    assert state.turn == state.player2.id


def test_dreepy_unavailable_without_energy():
    dreepy = make_card("TWM-128")
    defender = make_card("PAF-007")
    state = make_state(PlayerZones(active=[dreepy]), PlayerZones(active=[defender]))

    assert [a for a in dreepy.get_actions(state) if isinstance(a, AttackAction)] == []


@pytest.mark.card("TWM-129")
@pytest.mark.card_coverage(
    "TWM-129",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_drakloak_recon_directive_puts_top_card_in_hand():
    drakloak = make_card("TWM-129")
    top_card = make_card("PAF-007")
    second_card = make_card("PAF-008")
    state = make_state(
        PlayerZones(left=[top_card, second_card], active=[drakloak])
    )
    state.player1.onceUsedTurn["Recon Directive"] = False

    ability_actions = [a for a in drakloak.get_actions(state) if isinstance(a, UseAbilityAction)]
    assert len(ability_actions) == 1

    drive_choices(
        drakloak.reduce_action(ability_actions[0], state),
        [lambda _info: [top_card]],
    )

    assert top_card in state.player1.hand
    assert second_card is state.player1.left[-1]  # moved to bottom
    assert drakloak.abilityUsed is True


def test_drakloak_recon_directive_unavailable_after_use():
    drakloak = make_card("TWM-129")
    state = make_state(PlayerZones(left=[make_card("PAF-007"), make_card("PAF-008")], active=[drakloak]))
    drakloak.abilityUsed = True

    assert [a for a in drakloak.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_drakloak_dragon_headbutt_damages_opponent():
    drakloak = make_card("TWM-129")
    drakloak.energy = [CardType.FIRE, CardType.PSYCHIC]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], prize=[make_card("SVE-004")], active=[drakloak]),
        PlayerZones(left=[make_card("SVE-005")], prize=[make_card("SVE-007")], active=[defender]),
    )
    state.player1.onceUsedTurn["Recon Directive"] = False

    attacks = [a for a in drakloak.get_actions(state) if isinstance(a, AttackAction)]
    assert len(attacks) == 1

    list(drakloak.reduce_action(attacks[0], state))

    assert defender.hp == 260  # 330 - 70
    assert state.turn == state.player2.id


@pytest.mark.card("TWM-095")
@pytest.mark.card_coverage(
    "TWM-095",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "damage",
    "ability",
)
def test_munkidori_adrena_brain_moves_damage_counters_to_opponent():
    munkidori = make_card("TWM-095")
    munkidori.energy = [CardType.DARK]
    my_damaged = make_card("PAF-007")
    my_damaged.hp = 40  # has 3 damage counters (70 - 30 = 40)
    opp_active = make_card("PAF-054")
    state = make_state(
        PlayerZones(active=[munkidori], bench=[my_damaged]),
        PlayerZones(left=[make_card("SVE-005")], prize=[make_card("SVE-007")], active=[opp_active]),
    )
    state.player1.onceUsedTurn["Adrena-Brain"] = False

    ability_actions = [a for a in munkidori.get_actions(state) if isinstance(a, UseAbilityAction)]
    assert len(ability_actions) == 1

    drive_choices(
        munkidori.reduce_action(ability_actions[0], state),
        [lambda _info: [my_damaged], lambda _info: [opp_active]],
    )

    assert my_damaged.hp == 70   # restored (moved 3 counters off)
    assert opp_active.hp == 300  # 330 - 30 (3 counters * 10)
    assert munkidori.abilityUsed is True


def test_munkidori_adrena_brain_unavailable_without_dark_energy():
    munkidori = make_card("TWM-095")
    munkidori.energy = [CardType.PSYCHIC]
    opp_active = make_card("PAF-054")
    state = make_state(
        PlayerZones(active=[munkidori]),
        PlayerZones(active=[opp_active]),
    )
    state.player1.onceUsedTurn["Adrena-Brain"] = False

    assert [a for a in munkidori.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_munkidori_mind_bend_damages_opponent():
    munkidori = make_card("TWM-095")
    munkidori.energy = [CardType.PSYCHIC, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], prize=[make_card("SVE-004")], active=[munkidori]),
        PlayerZones(left=[make_card("SVE-005")], prize=[make_card("SVE-007")], active=[defender]),
    )
    state.player1.onceUsedTurn["Adrena-Brain"] = False

    attacks = [a for a in munkidori.get_actions(state) if isinstance(a, AttackAction)]
    assert len(attacks) == 1

    list(munkidori.reduce_action(attacks[0], state))

    assert defender.hp == 270  # 330 - 60
    assert state.turn == state.player2.id


@pytest.mark.card("TWM-200")
@pytest.mark.card_coverage(
    "TWM-200",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "damage",
)
def test_dragapult_ex_phantom_dive_damages_active_and_bench():
    dragapult = make_card("TWM-200")
    dragapult.energy = [CardType.FIRE, CardType.PSYCHIC]
    opp_active = make_card("PAF-054")
    opp_bench = make_card("PAF-007")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], prize=[make_card("SVE-004")], active=[dragapult]),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[opp_active],
            bench=[opp_bench],
        ),
    )

    attacks = [a for a in dragapult.get_actions(state) if isinstance(a, AttackAction) and a.attack.name == "Phantom Dive"]
    assert len(attacks) == 1

    drive_choices(
        dragapult.reduce_action(attacks[0], state),
        [lambda _info: [opp_bench]] * 6,
    )

    assert opp_active.hp == 130   # 330 - 200
    assert opp_bench.hp == 10     # 70 - 60 (6 counters * 10)
    assert state.turn == state.player2.id


def test_dragapult_ex_jet_headbutt_damages_opponent():
    dragapult = make_card("TWM-200")
    dragapult.energy = [CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(left=[make_card("SVE-002")], prize=[make_card("SVE-004")], active=[dragapult]),
        PlayerZones(left=[make_card("SVE-005")], prize=[make_card("SVE-007")], active=[defender]),
    )

    attacks = [a for a in dragapult.get_actions(state) if isinstance(a, AttackAction) and a.attack.name == "Jet Headbutt"]
    assert len(attacks) == 1

    list(dragapult.reduce_action(attacks[0], state))

    assert defender.hp == 260  # 330 - 70


def test_dragapult_ex_unavailable_without_energy():
    dragapult = make_card("TWM-200")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[dragapult]), PlayerZones(active=[defender]))

    assert [a for a in dragapult.get_actions(state) if isinstance(a, AttackAction)] == []
