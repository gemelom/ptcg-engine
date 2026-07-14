import pytest

from ptcg.core.action import AttackAction, UseAbilityAction
from ptcg.core.enums import CardTag, CardType, PlayerId
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("SIT-068")
@pytest.mark.card_coverage(
    "SIT-068",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
    "ability",
)
def test_kirlia_refinement_discards_one_card_and_draws_two():
    kirlia = make_card("SIT-068")
    discard_cost = make_card("PAF-084")
    drawn_cards = [make_card("SVE-002"), make_card("SVE-004")]
    remaining_card = make_card("SVE-005")
    state = make_state(
        PlayerZones(
            hand=[discard_cost],
            left=drawn_cards + [remaining_card],
            active=[kirlia],
        )
    )
    state.player1.onceUsedTurn["Refinement"] = False

    actions = kirlia.get_actions(state)
    ability_actions = [action for action in actions if isinstance(action, UseAbilityAction)]
    assert len(ability_actions) == 1

    prompts = drive_choices(
        kirlia.reduce_action(ability_actions[0], state),
        [lambda _info: [discard_cost]],
    )

    assert prompts[0]["prompt"].source is kirlia
    assert prompts[0]["prompt"].candidates == [discard_cost]
    assert state.player1.hand == drawn_cards
    assert state.player1.left == [remaining_card]
    assert state.player1.discard == [discard_cost]
    assert kirlia.abilityUsed is True
    assert state.player1.onceUsedTurn["Refinement"] is True


def test_kirlia_refinement_unavailable_without_hand_card():
    kirlia = make_card("SIT-068")
    state = make_state(PlayerZones(active=[kirlia]))
    state.player1.onceUsedTurn["Refinement"] = False

    assert [
        action for action in kirlia.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_kirlia_refinement_unavailable_after_use():
    kirlia = make_card("SIT-068")
    state = make_state(PlayerZones(hand=[make_card("PAF-084")], active=[kirlia]))
    state.player1.onceUsedTurn["Refinement"] = True

    assert [
        action for action in kirlia.get_actions(state) if isinstance(action, UseAbilityAction)
    ] == []


def test_kirlia_slap_damages_opponents_active_pokemon():
    kirlia = make_card("SIT-068")
    kirlia.energy = [CardType.PSYCHIC, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[kirlia],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Refinement"] = False

    slap = [
        action
        for action in kirlia.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Slap"
    ]
    assert len(slap) == 1

    list(kirlia.reduce_action(slap[0], state))

    assert defender.hp == 300
    assert state.turn == state.player2.id


def test_kirlia_slap_unavailable_without_energy():
    kirlia = make_card("SIT-068")
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[kirlia]), PlayerZones(active=[defender]))
    state.player1.onceUsedTurn["Refinement"] = False

    assert [
        action for action in kirlia.get_actions(state) if isinstance(action, AttackAction)
    ] == []


@pytest.mark.card("SIT-138")
@pytest.mark.card_coverage(
    "SIT-138",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "damage",
)
def test_lugia_v_read_ahead_draws_to_six_then_attaches_psychic_energy_to_bench():
    lugia = make_card("SIT-138")
    lugia.energy = [CardType.COLORLESS]
    hand_cards = [
        make_card("PAF-084"),
        make_card("PAF-089"),
        make_card("SVE-002"),
        make_card("SVE-004"),
    ]
    psychic_energy = make_card("SVE-005")
    drawn_card = make_card("SVE-008")
    remaining_deck_card = make_card("PAF-080")
    benched = make_card("PAF-007")
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            hand=hand_cards,
            left=[psychic_energy, drawn_card, remaining_deck_card],
            prize=[make_card("SVE-007")],
            active=[lugia],
            bench=[benched],
        ),
        PlayerZones(
            left=[make_card("PAF-080")],
            prize=[make_card("PAF-087")],
            active=[defender],
        ),
    )

    read_ahead = [
        action
        for action in lugia.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Read Ahead"
    ]
    assert len(read_ahead) == 1

    prompts = drive_choices(
        lugia.reduce_action(read_ahead[0], state),
        [
            lambda _info: [psychic_energy],
            lambda _info: [benched],
        ],
    )

    assert prompts[0]["prompt"].source is lugia
    assert prompts[0]["prompt"].candidates == [psychic_energy]
    assert prompts[1]["prompt"].source is lugia
    assert prompts[1]["prompt"].candidates == [benched]
    assert state.player1.hand == hand_cards + [drawn_card]
    assert state.player1.left == [remaining_deck_card]
    assert psychic_energy in benched.attachment
    assert benched.energy == [CardType.PSYCHIC]
    assert defender.hp == 330
    assert state.turn == state.player2.id


def test_lugia_v_aero_dive_discards_stadium_and_damages_opponents_active():
    lugia = make_card("SIT-138")
    lugia.energy = [
        CardType.COLORLESS,
        CardType.COLORLESS,
        CardType.COLORLESS,
        CardType.COLORLESS,
    ]
    stadium = make_card("OBF-196")
    stadium.playedFrom = PlayerId.PLAYER1
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[lugia],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.firstTurn = False
    state.stadium = [stadium]

    aero_dive = [
        action
        for action in lugia.get_actions(state)
        if isinstance(action, AttackAction) and action.attack.name == "Aero Dive"
    ]
    assert len(aero_dive) == 1

    prompts = drive_choices(
        lugia.reduce_action(aero_dive[0], state),
        [lambda _info: [stadium]],
    )

    assert prompts[0]["prompt"].source is lugia
    assert prompts[0]["prompt"].candidates == [stadium]
    assert state.stadium == []
    assert state.player1.discard == [stadium]
    assert defender.hp == 200
    assert state.turn == state.player2.id


def test_lugia_v_aero_dive_unavailable_on_first_turn():
    lugia = make_card("SIT-138")
    lugia.energy = [
        CardType.COLORLESS,
        CardType.COLORLESS,
        CardType.COLORLESS,
        CardType.COLORLESS,
    ]
    defender = make_card("PAF-054")
    state = make_state(PlayerZones(active=[lugia]), PlayerZones(active=[defender]))

    assert [
        action.attack.name
        for action in lugia.get_actions(state)
        if isinstance(action, AttackAction)
    ] == ["Read Ahead"]


@pytest.mark.card("SIT-139")
@pytest.mark.card_coverage(
    "SIT-139",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "ability",
)
def test_lugia_vstar_summoning_star_puts_colorless_pokemon_on_bench():
    lugia = make_card("SIT-139")
    colorless1 = make_card("BRS-124")  # Minccino - Colorless Basic
    colorless2 = make_card("SIT-138")  # Lugia V - Colorless Basic
    state = make_state(
        PlayerZones(
            discard=[colorless1, colorless2],
            active=[lugia],
        )
    )
    state.player1.onceUsedGame[CardTag.VSTAR] = False

    ability_actions = [a for a in lugia.get_actions(state) if isinstance(a, UseAbilityAction)]
    assert len(ability_actions) == 1

    prompts = drive_choices(
        lugia.reduce_action(ability_actions[0], state),
        [lambda _info: [colorless1, colorless2]],
    )

    assert prompts[0]["prompt"].source is lugia
    assert set(prompts[0]["prompt"].candidates) == {colorless1, colorless2}
    assert len(state.player1.bench) == 2
    assert state.player1.onceUsedGame[CardTag.VSTAR] is True


def test_lugia_vstar_summoning_star_unavailable_when_vstar_used():
    lugia = make_card("SIT-139")
    colorless = make_card("BRS-124")
    state = make_state(PlayerZones(discard=[colorless], active=[lugia]))
    state.player1.onceUsedGame[CardTag.VSTAR] = True

    assert [a for a in lugia.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_lugia_vstar_summoning_star_unavailable_without_colorless_in_discard():
    lugia = make_card("SIT-139")
    non_colorless = make_card("PAF-054")  # Charizard ex - Fire type
    state = make_state(PlayerZones(discard=[non_colorless], active=[lugia]))
    state.player1.onceUsedGame[CardTag.VSTAR] = False

    assert [a for a in lugia.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_lugia_vstar_tempest_dive_damages_opponent():
    lugia = make_card("SIT-139")
    lugia.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[lugia],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.onceUsedGame[CardTag.VSTAR] = False

    attacks = [a for a in lugia.get_actions(state) if isinstance(a, AttackAction)]
    assert len(attacks) == 1

    list(lugia.reduce_action(attacks[0], state))

    assert defender.hp == 200  # 330 - 130
    assert state.turn == state.player2.id


@pytest.mark.card("SIT-147")
@pytest.mark.card_coverage(
    "SIT-147",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
    "ability",
)
def test_archeops_primal_turbo_attaches_special_energy_to_pokemon():
    archeops = make_card("SIT-147")
    special1 = make_card("BRS-151")  # Double Turbo Energy
    special2 = make_card("SIT-169")  # V Guard Energy
    benched = make_card("BRS-124")   # Minccino
    state = make_state(
        PlayerZones(
            left=[special1, special2],
            active=[archeops],
            bench=[benched],
        )
    )
    state.player1.onceUsedTurn["Primal Turbo"] = False

    ability_actions = [a for a in archeops.get_actions(state) if isinstance(a, UseAbilityAction)]
    assert len(ability_actions) == 1

    prompts = drive_choices(
        archeops.reduce_action(ability_actions[0], state),
        [lambda _info: [special1, special2], lambda _info: [benched]],
    )

    assert prompts[0]["prompt"].source is archeops
    assert set(prompts[0]["prompt"].candidates) == {special1, special2}
    assert prompts[1]["prompt"].source is archeops
    assert special1 in benched.attachment
    assert special2 in benched.attachment
    assert archeops.abilityUsed is True
    assert state.player1.onceUsedTurn["Primal Turbo"] is True


def test_archeops_primal_turbo_unavailable_without_special_energy_in_deck():
    archeops = make_card("SIT-147")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],  # Basic energy, not special
            active=[archeops],
        )
    )
    state.player1.onceUsedTurn["Primal Turbo"] = False

    assert [a for a in archeops.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_archeops_primal_turbo_unavailable_after_use():
    archeops = make_card("SIT-147")
    state = make_state(
        PlayerZones(left=[make_card("BRS-151")], active=[archeops])
    )
    state.player1.onceUsedTurn["Primal Turbo"] = True

    assert [a for a in archeops.get_actions(state) if isinstance(a, UseAbilityAction)] == []


def test_archeops_speed_wing_damages_opponent():
    archeops = make_card("SIT-147")
    archeops.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    defender = make_card("PAF-054")
    state = make_state(
        PlayerZones(
            left=[make_card("SVE-002")],
            prize=[make_card("SVE-004")],
            active=[archeops],
        ),
        PlayerZones(
            left=[make_card("SVE-005")],
            prize=[make_card("SVE-007")],
            active=[defender],
        ),
    )
    state.player1.onceUsedTurn["Primal Turbo"] = False

    attacks = [a for a in archeops.get_actions(state) if isinstance(a, AttackAction)]
    assert len(attacks) == 1

    list(archeops.reduce_action(attacks[0], state))

    assert defender.hp == 210  # 330 - 120
    assert state.turn == state.player2.id
