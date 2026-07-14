import pytest

from ptcg.core.action import AttackAction, UseToolAction
from ptcg.core.enums import CardPosition, PokemonPosition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAR-166")
@pytest.mark.card_coverage(
    "PAR-166",
    "get_actions",
    "reduce_action",
    "negative_case",
    "zone_change",
)
def test_luxurious_cape_attaches_to_no_rule_box_pokemon_and_adds_hp():
    luxurious_cape = make_card("PAR-166")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[luxurious_cape], active=[charmander]))
    starting_hp = charmander.hp

    actions = luxurious_cape.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseToolAction)
    assert actions[0].target is charmander

    luxurious_cape.reduce_action(actions[0], state)

    assert luxurious_cape in charmander.attachment
    assert luxurious_cape not in state.player1.hand
    assert luxurious_cape.hasAttached is True
    assert luxurious_cape.attachedTo == [charmander]
    assert charmander.hp == starting_hp + 100
    assert luxurious_cape.get_actions(state) == []


def test_luxurious_cape_is_unavailable_for_pokemon_with_rule_box():
    luxurious_cape = make_card("PAR-166")
    radiant_greninja = make_card("ASR-046")
    state = make_state(PlayerZones(hand=[luxurious_cape], active=[radiant_greninja]))

    assert luxurious_cape.get_actions(state) == []


def test_luxurious_cape_is_unavailable_when_pokemon_already_has_tool():
    luxurious_cape = make_card("PAR-166")
    charmander = make_card("PAF-007")
    charmander.attachment = [make_card("MEW-165")]
    state = make_state(PlayerZones(hand=[luxurious_cape], active=[charmander]))

    assert luxurious_cape.get_actions(state) == []


@pytest.mark.card("PAR-178")
@pytest.mark.card_coverage(
    "PAR-178",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_technical_machine_evolution_attaches_to_pokemon_without_tool():
    technical_machine = make_card("PAR-178")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[technical_machine], active=[charmander]))

    actions = technical_machine.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseToolAction)
    assert actions[0].target is charmander

    list(technical_machine.reduce_action(actions[0], state))

    assert technical_machine in charmander.attachment
    assert technical_machine not in state.player1.hand
    assert technical_machine.hasAttached is True
    assert technical_machine.attachedTo == [charmander]


def test_technical_machine_evolution_dangerous_evolution_evolves_attached_active_from_deck(
    monkeypatch,
):
    monkeypatch.setattr("ptcg.utils.utils.random.shuffle", lambda _cards: None)
    technical_machine = make_card("PAR-178")
    charmander = make_card("PAF-007")
    charmeleon = make_card("PAF-008")
    rare_candy = make_card("PAF-089")
    state = make_state(
        PlayerZones(
            left=[rare_candy, charmeleon],
            prize=[make_card("SVE-002")],
            active=[charmander],
        ),
        PlayerZones(
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-005")],
            active=[make_card("PAF-054")],
        ),
    )
    charmander.attachment = [technical_machine]
    technical_machine.hasAttached = True
    technical_machine.attachedTo = [charmander]

    attacks = [
        action
        for action in technical_machine.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Dangerous Evolution"
    ]
    assert len(attacks) == 1
    assert attacks[0].source is charmander

    prompts = drive_choices(
        technical_machine.reduce_action(attacks[0], state),
        [lambda _info: [charmeleon]],
    )

    assert prompts[0]["prompt"].source is technical_machine
    assert prompts[0]["prompt"].candidates == [charmeleon]
    assert state.player1.active == [charmeleon]
    assert charmander in charmeleon.evolved
    assert technical_machine in charmeleon.attachment
    assert charmeleon.cardPosition == CardPosition.ACTIVE
    assert charmeleon.position == PokemonPosition.ACTIVE
    assert state.player1.left == [rare_candy]
    assert state.turn == state.player2.id


def test_technical_machine_evolution_attack_unavailable_without_matching_evolution():
    technical_machine = make_card("PAR-178")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(left=[make_card("MEW-017")], active=[charmander]))
    charmander.attachment = [technical_machine]
    technical_machine.hasAttached = True
    technical_machine.attachedTo = [charmander]

    assert [
        action
        for action in technical_machine.get_actions(state)
        if isinstance(action, AttackAction)
    ] == []
