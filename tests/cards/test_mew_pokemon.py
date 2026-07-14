import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("MEW-016")
@pytest.mark.card_coverage(
    "MEW-016",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_pidgey_call_for_family_puts_two_basic_pokemon_from_deck_onto_bench(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    pidgey = make_card("MEW-016")
    pidgey.energy = [CardType.COLORLESS]
    charmander = make_card("PAF-007")
    scyther = make_card("MEW-123")
    pidgeotto = make_card("MEW-017")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[charmander, scyther, pidgeotto],
            prize=[make_card("SVE-002")],
            active=[pidgey],
        ),
        PlayerZones(
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-005")],
            active=[defender],
        ),
    )

    actions = pidgey.get_actions(state)
    call_for_family = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Call for Family"
    ]
    assert len(call_for_family) == 1

    prompts = drive_choices(
        pidgey.reduce_action(call_for_family[0], state),
        [lambda _info: [charmander, scyther]],
    )

    assert prompts[0]["prompt"].source is pidgey
    assert [card.name for card in prompts[0]["prompt"].candidates] == ["Charmander", "Scyther"]
    assert state.player1.bench == [charmander, scyther]
    assert pidgeotto in state.player1.left
    assert state.turn == state.player2.id


def test_pidgey_attacks_are_unavailable_without_energy():
    pidgey = make_card("MEW-016")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[pidgey]), PlayerZones(active=[defender]))

    assert [action for action in pidgey.get_actions(state) if isinstance(action, AttackAction)] == []


@pytest.mark.card("MEW-017")
@pytest.mark.card_coverage(
    "MEW-017",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_pidgeotto_flap_damages_opponents_active_pokemon():
    pidgeotto = make_card("MEW-017")
    pidgeotto.energy = [CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[pidgeotto],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    actions = pidgeotto.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1

    list(pidgeotto.reduce_action(attack_actions[0], state))

    assert defender.hp == 310


def test_pidgeotto_flap_unavailable_without_energy():
    pidgeotto = make_card("MEW-017")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[pidgeotto]), PlayerZones(active=[defender]))

    assert [action for action in pidgeotto.get_actions(state) if isinstance(action, AttackAction)] == []


@pytest.mark.card("MEW-123")
@pytest.mark.card_coverage(
    "MEW-123",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
    "damage",
)
def test_scyther_helpful_slash_attaches_grass_energy_from_discard_to_bench():
    scyther = make_card("MEW-123")
    scyther.energy = [CardType.GRASS]
    grass_energy = make_card("SVE-002")
    grass_energy.cardType = CardType.GRASS
    grass_energy.provides = [CardType.GRASS]
    benched = make_card("PAF-007")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-004")],
            discard=[grass_energy],
            prize=[make_card("SVE-005")],
            active=[scyther],
            bench=[benched],
        ),
        PlayerZones(
            left=[make_card("SVE-007")],
            prize=[make_card("SVE-008")],
            active=[defender],
        ),
    )

    actions = scyther.get_actions(state)
    helpful_slash = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Helpful Slash"
    ]
    assert len(helpful_slash) == 1

    list(scyther.reduce_action(helpful_slash[0], state))

    assert defender.hp == 290
    assert grass_energy in benched.attachment
    assert benched.energy == [CardType.GRASS]
    assert grass_energy not in state.player1.discard


def test_scyther_attacks_are_unavailable_without_energy():
    scyther = make_card("MEW-123")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[scyther]), PlayerZones(active=[defender]))

    assert [action for action in scyther.get_actions(state) if isinstance(action, AttackAction)] == []


@pytest.mark.card("MEW-151")
@pytest.mark.card_coverage(
    "MEW-151",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_mew_ex_restart_draws_until_hand_has_three_cards():
    mew = make_card("MEW-151")
    hand_card = make_card("SVE-002")
    drawn_cards = [make_card("SVE-004"), make_card("SVE-005")]
    state = make_state(PlayerZones(hand=[hand_card], left=drawn_cards, active=[mew]))
    state.player1.onceUsedTurn["Restart"] = False

    actions = mew.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    list(mew.reduce_action(ability_actions[0], state))

    assert state.player1.hand == [hand_card] + drawn_cards
    assert state.player1.left == []
    assert mew.abilityUsed is True
    assert state.player1.onceUsedTurn["Restart"] is True


def test_mew_ex_genome_hacking_copies_opponents_active_attack_damage():
    mew = make_card("MEW-151")
    mew.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("MEW-017")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[mew],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Restart"] = False

    actions = mew.get_actions(state)
    genome_hacking = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Genome Hacking"
    ]
    assert len(genome_hacking) == 1

    prompts = drive_choices(
        mew.reduce_action(genome_hacking[0], state),
        [lambda _info: [defender.attacks[0]]],
    )

    assert prompts[0]["prompt"].source is mew
    assert [attack.name for attack in prompts[0]["prompt"].candidates] == ["Flap"]
    assert defender.hp == 60


def test_mew_ex_restart_unavailable_after_use():
    mew = make_card("MEW-151")
    state = make_state(PlayerZones(active=[mew]))
    state.player1.onceUsedTurn["Restart"] = True

    assert [action for action in mew.get_actions(state) if isinstance(action, UseAbilityAction)] == []
