import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardType
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("OBF-080")
@pytest.mark.card_coverage("OBF-080", "get_actions", "reduce_action", "zone_change")
def test_cleffa_grasping_draw_draws_until_hand_has_seven_cards_and_ends_turn():
    cleffa = make_card("OBF-080")
    hand_cards = [make_card("SVE-002"), make_card("SVE-004")]
    drawn_cards = [
        make_card("SVE-005"),
        make_card("SVE-007"),
        make_card("SVE-008"),
        make_card("PAF-007"),
        make_card("PAF-008"),
    ]
    remaining_card = make_card("PAF-027")
    state = make_state(
        PlayerZones(
            hand=hand_cards,
            left=drawn_cards + [remaining_card],
            prize=[make_card("PAF-084")],
            active=[cleffa],
        ),
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[make_card("PAF-054")],
        ),
    )

    actions = cleffa.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1
    assert attack_actions[0].attack.name == "Grasping Draw"

    list(cleffa.reduce_action(attack_actions[0], state))

    assert state.player1.hand == hand_cards + drawn_cards
    assert state.player1.left == [remaining_card]
    assert state.turn == state.player2.id


def test_cleffa_grasping_draw_does_not_draw_when_hand_has_seven_cards():
    cleffa = make_card("OBF-080")
    hand_cards = [make_card("SVE-002") for _ in range(7)]
    deck_card = make_card("SVE-004")
    state = make_state(
        PlayerZones(
            hand=hand_cards,
            left=[deck_card],
            prize=[make_card("SVE-005")],
            active=[cleffa],
        ),
        PlayerZones(
            left=[make_card("SVE-007")],
            prize=[make_card("SVE-008")],
            active=[make_card("PAF-054")],
        ),
    )

    list(cleffa.reduce_action(cleffa.get_actions(state)[0], state))

    assert state.player1.hand == hand_cards
    assert state.player1.left == [deck_card]


@pytest.mark.card("OBF-026")
@pytest.mark.card_coverage(
    "OBF-026",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_obf_charmander_heat_tackle_damages_target_and_itself():
    charmander = make_card("OBF-026")
    charmander.energy = [CardType.FIRE]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[charmander],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )

    actions = charmander.get_actions(state)
    attack_actions = [action for action in actions if isinstance(action, AttackAction)]
    assert len(attack_actions) == 1

    list(charmander.reduce_action(attack_actions[0], state))

    assert defender.hp == 300
    assert charmander.hp == 50


def test_obf_charmander_heat_tackle_unavailable_without_fire_energy():
    charmander = make_card("OBF-026")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[charmander]), PlayerZones(active=[defender]))

    assert [action for action in charmander.get_actions(state) if isinstance(action, AttackAction)] == []


@pytest.mark.card("OBF-141")
@pytest.mark.card_coverage(
    "OBF-141",
    "get_actions",
    "reduce_action",
    "negative_case",
    "damage",
)
def test_scizor_punishing_scissors_adds_damage_for_opponents_pokemon_with_abilities():
    scizor = make_card("OBF-141")
    scizor.energy = [CardType.METAL]
    defender = make_card("PAF-054")
    ability_bench = make_card("BRS-048")
    no_ability_bench = make_card("PAF-007")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[scizor],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
            bench=[ability_bench, no_ability_bench],
        ),
    )

    actions = scizor.get_actions(state)
    punishing_scissors = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Punishing Scissors"
    ]
    assert len(punishing_scissors) == 1

    list(scizor.reduce_action(punishing_scissors[0], state))

    assert punishing_scissors[0].attack.damage == 110
    assert defender.hp == 220


def test_scizor_cut_unavailable_without_second_energy():
    scizor = make_card("OBF-141")
    scizor.energy = [CardType.METAL]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[scizor]), PlayerZones(active=[defender]))

    assert [
        action.attack.name
        for action in scizor.get_actions(state)
        if isinstance(action, AttackAction)
    ] == ["Punishing Scissors"]


@pytest.mark.card("OBF-164")
@pytest.mark.card_coverage(
    "OBF-164",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_pidgeot_ex_quick_search_puts_one_card_from_deck_into_hand(monkeypatch):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    pidgeot = make_card("OBF-164")
    chosen_card = make_card("PAF-084")
    other_card = make_card("SVE-002")
    state = make_state(PlayerZones(left=[chosen_card, other_card], active=[pidgeot]))
    state.player1.onceUsedTurn["Quick Search"] = False

    actions = pidgeot.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    prompts = drive_choices(
        pidgeot.reduce_action(ability_actions[0], state),
        [lambda _info: [chosen_card]],
    )

    assert prompts[0]["prompt"].source is pidgeot
    assert prompts[0]["prompt"].candidates == [chosen_card, other_card]
    assert state.player1.hand == [chosen_card]
    assert state.player1.left == [other_card]
    assert pidgeot.abilityUsed is True
    assert state.player1.onceUsedTurn["Quick Search"] is True


def test_pidgeot_ex_quick_search_unavailable_after_use():
    pidgeot = make_card("OBF-164")
    state = make_state(PlayerZones(left=[make_card("PAF-084")], active=[pidgeot]))
    state.player1.onceUsedTurn["Quick Search"] = True

    assert [
        action for action in pidgeot.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_pidgeot_ex_blustery_wind_damages_opponents_active_pokemon():
    pidgeot = make_card("OBF-164")
    pidgeot.energy = [CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[pidgeot],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Quick Search"] = False

    actions = pidgeot.get_actions(state)
    blustery_wind = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Blustery Wind"
    ]
    assert len(blustery_wind) == 1

    list(pidgeot.reduce_action(blustery_wind[0], state))

    assert defender.hp == 210
    assert state.turn == state.player2.id
