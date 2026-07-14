import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardPosition, CardType
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAL-264")
@pytest.mark.card_coverage(
    "PAL-264",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_squawkabilly_ex_squawk_and_seize_discards_hand_and_draws_six():
    squawkabilly = make_card("PAL-264")
    discarded_cards = [make_card("PAF-084"), make_card("PAF-089")]
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
            hand=discarded_cards,
            left=drawn_cards + [remaining_card],
            active=[squawkabilly],
        )
    )
    state.player1.onceUsedTurn["Squawk and Seize"] = False

    actions = squawkabilly.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    list(squawkabilly.reduce_action(ability_actions[0], state))

    assert state.player1.hand == drawn_cards
    assert state.player1.left == [remaining_card]
    assert state.player1.discard == discarded_cards
    assert squawkabilly.abilityUsed is True
    assert state.player1.onceUsedTurn["Squawk and Seize"] is True


def test_squawkabilly_ex_squawk_and_seize_unavailable_after_first_turn():
    squawkabilly = make_card("PAL-264")
    state = make_state(PlayerZones(active=[squawkabilly]))
    state.player1.firstTurn = False
    state.player1.onceUsedTurn["Squawk and Seize"] = False

    assert [
        action for action in squawkabilly.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_squawkabilly_ex_motivate_attaches_two_basic_energy_to_benched_pokemon():
    squawkabilly = make_card("PAL-264")
    squawkabilly.energy = [CardType.COLORLESS]
    fire_energy = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    rare_candy = make_card("PAF-089")
    benched = make_card("PAF-007")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            discard=[fire_energy, lightning_energy, rare_candy],
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[squawkabilly],
            bench=[benched],
        ),
        PlayerZones(
            left=[make_card("SVE-008")],
            prize=[make_card("PAF-084")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Squawk and Seize"] = False

    actions = squawkabilly.get_actions(state)
    motivate = [
        action
        for action in actions
        if isinstance(action, AttackAction) and action.attack.name == "Motivate"
    ]
    assert len(motivate) == 1

    prompts = drive_choices(
        squawkabilly.reduce_action(motivate[0], state),
        [
            lambda _info: [fire_energy, lightning_energy],
            lambda _info: [benched],
        ],
    )

    assert prompts[0]["prompt"].source is squawkabilly
    assert prompts[0]["prompt"].candidates == [fire_energy, lightning_energy]
    assert prompts[1]["prompt"].source is squawkabilly
    assert prompts[1]["prompt"].candidates == [benched]
    assert fire_energy in benched.attachment
    assert lightning_energy in benched.attachment
    assert fire_energy not in state.player1.discard
    assert lightning_energy not in state.player1.discard
    assert rare_candy in state.player1.discard
    assert benched.energy == [CardType.FIRE, CardType.LIGHTNING]
    assert defender.hp == 310
    assert state.turn == state.player2.id
    assert squawkabilly.cardPosition == CardPosition.ACTIVE


def test_squawkabilly_ex_motivate_unavailable_without_energy():
    squawkabilly = make_card("PAL-264")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[squawkabilly]), PlayerZones(active=[defender]))
    state.player1.onceUsedTurn["Squawk and Seize"] = False

    assert [
        action for action in squawkabilly.get_actions(state) if isinstance(action, AttackAction)
    ] == []
