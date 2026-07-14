import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardType, PlayerId
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("CRZ-045")
@pytest.mark.card_coverage(
    "CRZ-045",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_rotom_v_instant_charge_draws_three_cards_and_ends_turn():
    rotom = make_card("CRZ-045")
    drawn_cards = [make_card("SVE-002"), make_card("SVE-004"), make_card("SVE-005")]
    remaining_card = make_card("SVE-007")
    state = make_state(
        PlayerZones(
            left=drawn_cards + [remaining_card],
            prize=[make_card("SVE-008")],
            active=[rotom],
        ),
        PlayerZones(
            left=[make_card("PAF-007")],
            prize=[make_card("PAF-008")],
            active=[make_card("PAF-054")],
        ),
    )

    actions = rotom.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    list(rotom.reduce_action(ability_actions[0], state))

    assert state.player1.hand == drawn_cards
    assert state.player1.left == [remaining_card]
    assert state.turn == state.player2.id


def test_rotom_v_scrap_short_lost_zones_tools_for_extra_damage():
    rotom = make_card("CRZ-045")
    rotom.energy = [CardType.LIGHTNING, CardType.LIGHTNING]
    rigid_band = make_card("MEW-165")
    rescue_board = make_card("TEF-159")
    non_tool = make_card("SVE-002")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-004")],
            discard=[rigid_band, rescue_board, non_tool],
            prize=[make_card("SVE-005")],
            active=[rotom],
        ),
        PlayerZones(
            left=[make_card("SVE-007")],
            prize=[make_card("SVE-008")],
            active=[defender],
        ),
    )

    actions = rotom.get_actions(state)
    scrap_short = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Scrap Short"
    ]
    assert len(scrap_short) == 1

    prompts = drive_choices(
        rotom.reduce_action(scrap_short[0], state),
        [lambda _info: [rigid_band, rescue_board]],
    )

    assert prompts[0]["prompt"].source is rotom
    assert [card.name for card in prompts[0]["prompt"].candidates] == [
        "Rigid Band",
        "Rescue Board",
    ]
    assert scrap_short[0].attack.damage == 120
    assert defender.hp == 210
    assert rigid_band in state.player1.lostZone
    assert rescue_board in state.player1.lostZone
    assert non_tool in state.player1.discard


def test_rotom_v_scrap_short_unavailable_without_lightning_energy():
    rotom = make_card("CRZ-045")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[rotom]), PlayerZones(active=[defender]))

    assert [action for action in rotom.get_actions(state) if isinstance(action, AttackAction)] == []


@pytest.mark.card("CRZ-111")
@pytest.mark.card_coverage(
    "CRZ-111",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
    "ability",
)
def test_bidoof_hyper_fang_deals_damage_on_heads(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.randint", lambda _start, _end: 0)
    bidoof = make_card("CRZ-111")
    bidoof.energy = [CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[bidoof],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    actions = bidoof.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1

    list(bidoof.reduce_action(attack_actions[0], state))

    assert defender.hp == 300
    assert state.auto_events[0] == "Coin flip: HEADS."


def test_bidoof_hyper_fang_unavailable_without_two_energy():
    bidoof = make_card("CRZ-111")
    bidoof.energy = [CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[bidoof]), PlayerZones(active=[defender]))

    assert [action for action in bidoof.get_actions(state) if isinstance(action, AttackAction)] == []


def test_bidoof_carefree_countenance_zeroes_damage_when_targeted_on_bench():
    bidoof = make_card("CRZ-111")
    attacker = make_card("ASR-046")
    state = make_state(
        PlayerZones(bench=[bidoof]),
        PlayerZones(active=[attacker]),
        turn=PlayerId.PLAYER2,
    )
    action = AttackAction(state.player2.id, attacker, attacker.attacks[0], bidoof)
    action.attack.damage = 90

    bidoof.use_ability(action, state)

    assert action.attack.damage == 0


@pytest.mark.card("CRZ-020")
@pytest.mark.card_coverage(
    "CRZ-020",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
    "ability",
)
def test_radiant_charizard_excited_heart_reduces_combustion_blast_cost():
    charizard = make_card("CRZ-020")
    charizard.energy = [CardType.FIRE, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[charizard],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007") for _ in range(4)],
            active=[defender],
        ),
    )

    actions = charizard.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1
    assert attack_actions[0].attack.name == "Combustion Blast"

    list(charizard.reduce_action(attack_actions[0], state))

    assert defender.hp == 80
    assert charizard.useAttackLastTurn is True


def test_radiant_charizard_combustion_blast_unavailable_when_used_last_turn():
    charizard = make_card("CRZ-020")
    charizard.energy = [
        CardType.FIRE,
        CardType.COLORLESS,
        CardType.COLORLESS,
        CardType.COLORLESS,
        CardType.COLORLESS,
    ]
    charizard.useAttackLastTurn = True
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[charizard]), PlayerZones(active=[defender]))

    assert [action for action in charizard.get_actions(state) if isinstance(action, AttackAction)] == []
