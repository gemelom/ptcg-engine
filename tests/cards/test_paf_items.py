import pytest

from ptcg.core.action import UseItemAction
from ptcg.core.action import UseSupporterAction
from ptcg.core.enums import CardPosition, PokemonPosition
from tests.helpers.cards import make_card
from tests.helpers.generator_driver import drive_choices
from tests.helpers.state_builder import PlayerZones, make_state


@pytest.mark.card("PAF-084")
@pytest.mark.card_coverage(
    "PAF-084",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_nest_ball_puts_basic_pokemon_from_deck_onto_bench():
    nest_ball = make_card("PAF-084")
    charmander = make_card("PAF-007")
    charmeleon = make_card("PAF-008")
    state = make_state(PlayerZones(hand=[nest_ball], left=[charmander, charmeleon]))

    actions = nest_ball.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        nest_ball.reduce_action(actions[0], state),
        [lambda _info: [charmander]],
    )

    assert prompts[0]["prompt"].source is nest_ball
    assert [card.name for card in prompts[0]["prompt"].candidates] == ["Charmander"]
    assert nest_ball in state.player1.discard
    assert charmander in state.player1.bench
    assert charmander not in state.player1.left
    assert charmander.cardPosition == CardPosition.BENCH
    assert charmander.position == PokemonPosition.BENCH
    assert charmeleon in state.player1.left


def test_nest_ball_is_unavailable_when_bench_is_full():
    nest_ball = make_card("PAF-084")
    bench = [make_card("PAF-007") for _ in range(5)]
    state = make_state(PlayerZones(hand=[nest_ball], bench=bench))

    assert nest_ball.get_actions(state) == []


@pytest.mark.card("PAF-091")
@pytest.mark.card_coverage(
    "PAF-091",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_ultra_ball_discards_two_cards_then_searches_pokemon_to_hand():
    ultra_ball = make_card("PAF-091")
    fire_energy = make_card("SVE-002")
    lightning_energy = make_card("SVE-004")
    charmander = make_card("PAF-007")
    rare_candy = make_card("PAF-089")
    state = make_state(
        PlayerZones(
            hand=[ultra_ball, fire_energy, lightning_energy],
            left=[charmander, rare_candy],
        )
    )

    actions = ultra_ball.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        ultra_ball.reduce_action(actions[0], state),
        [
            lambda _info: [fire_energy, lightning_energy],
            lambda _info: [charmander],
        ],
    )

    assert prompts[0]["prompt"].source is ultra_ball
    assert sorted(card.name for card in prompts[0]["prompt"].candidates) == [
        "Fire Energy",
        "Lightning Energy",
    ]
    assert prompts[1]["prompt"].source is ultra_ball
    assert [card.name for card in prompts[1]["prompt"].candidates] == ["Charmander"]
    assert ultra_ball in state.player1.discard
    assert fire_energy in state.player1.discard
    assert lightning_energy in state.player1.discard
    assert charmander in state.player1.hand
    assert rare_candy in state.player1.left


def test_ultra_ball_is_unavailable_without_two_other_hand_cards():
    ultra_ball = make_card("PAF-091")
    fire_energy = make_card("SVE-002")
    state = make_state(PlayerZones(hand=[ultra_ball, fire_energy]))

    assert ultra_ball.get_actions(state) == []


@pytest.mark.card("PAF-087")
@pytest.mark.card_coverage("PAF-087", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_professors_research_discards_hand_and_draws_seven_cards():
    professors_research = make_card("PAF-087")
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
    ]
    state = make_state(
        PlayerZones(
            hand=[professors_research, fire_energy, lightning_energy],
            left=drawn_cards,
        )
    )

    actions = professors_research.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseSupporterAction)

    professors_research.reduce_action(actions[0], state)

    assert state.player1.hand == drawn_cards
    assert professors_research in state.player1.discard
    assert fire_energy in state.player1.discard
    assert lightning_energy in state.player1.discard
    assert state.player1.left == []
    assert state.player1.supporterPlayedTurn is True


def test_professors_research_is_unavailable_after_supporter_played():
    professors_research = make_card("PAF-087")
    state = make_state(PlayerZones(hand=[professors_research]))
    state.player1.supporterPlayedTurn = True

    assert professors_research.get_actions(state) == []


@pytest.mark.card("PAF-080")
@pytest.mark.card_coverage("PAF-080", "get_actions", "reduce_action", "negative_case", "zone_change")
def test_iono_shuffles_hands_into_decks_and_draws_for_remaining_prizes():
    iono = make_card("PAF-080")
    player_hand_card = make_card("SVE-002")
    player_draw_1 = make_card("SVE-004")
    player_draw_2 = make_card("SVE-005")
    player_extra_deck_card = make_card("SVE-007")
    opponent_hand_card = make_card("SVE-008")
    opponent_draw = make_card("PAF-007")
    opponent_extra_deck_card = make_card("PAF-008")
    state = make_state(
        PlayerZones(
            hand=[iono, player_hand_card],
            left=[player_draw_1, player_draw_2, player_extra_deck_card],
            prize=[make_card("PAF-007"), make_card("PAF-007")],
        ),
        PlayerZones(
            hand=[opponent_hand_card],
            left=[opponent_draw, opponent_extra_deck_card],
            prize=[make_card("PAF-007")],
        ),
    )

    actions = iono.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseSupporterAction)

    iono.reduce_action(actions[0], state)

    assert iono in state.player1.discard
    assert state.player1.hand == [player_draw_1, player_draw_2]
    assert state.player2.hand == [opponent_draw]
    assert player_hand_card in state.player1.left
    assert opponent_hand_card in state.player2.left
    assert state.player1.supporterPlayedTurn is True
    assert state.player2.supporterPlayedTurn is True


def test_iono_is_unavailable_after_supporter_played():
    iono = make_card("PAF-080")
    state = make_state(PlayerZones(hand=[iono]))
    state.player1.supporterPlayedTurn = True

    assert iono.get_actions(state) == []


@pytest.mark.card("PAF-089")
@pytest.mark.card_coverage(
    "PAF-089",
    "get_actions",
    "reduce_action",
    "choice_flow",
    "negative_case",
    "zone_change",
)
def test_rare_candy_evolves_basic_pokemon_into_stage_two_from_hand():
    rare_candy = make_card("PAF-089")
    charizard_ex = make_card("PAF-054")
    charmander = make_card("PAF-007")
    charmander.firstTurnPlayed = False
    state = make_state(PlayerZones(hand=[rare_candy, charizard_ex], active=[charmander]))

    actions = rare_candy.get_actions(state)
    assert len(actions) == 1
    assert isinstance(actions[0], UseItemAction)

    prompts = drive_choices(
        rare_candy.reduce_action(actions[0], state),
        [
            lambda _info: [charizard_ex],
            lambda _info: [charmander],
            lambda _info: [],
        ],
    )

    assert prompts[0]["prompt"].source is rare_candy
    assert [card.name for card in prompts[0]["prompt"].candidates] == ["Charizard ex"]
    assert prompts[1]["prompt"].source is rare_candy
    assert [card.name for card in prompts[1]["prompt"].candidates] == ["Charmander"]
    assert prompts[2]["prompt"].source is charizard_ex
    assert prompts[2]["prompt"].candidates == []
    assert rare_candy in state.player1.discard
    assert state.player1.active == [charizard_ex]
    assert charmander in charizard_ex.evolved
    assert charizard_ex.cardPosition == CardPosition.ACTIVE
    assert charizard_ex.position == PokemonPosition.ACTIVE


def test_rare_candy_is_unavailable_for_basic_pokemon_played_this_turn():
    rare_candy = make_card("PAF-089")
    charizard_ex = make_card("PAF-054")
    charmander = make_card("PAF-007")
    state = make_state(PlayerZones(hand=[rare_candy, charizard_ex], active=[charmander]))

    assert rare_candy.get_actions(state) == []
