from __future__ import annotations

from ptcg import PokemonTCG
from ptcg.core.action import AttackAction, EvolvePokemonAction, UseSupporterAction
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PlayerId
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state

P1 = PlayerId.PLAYER1
P2 = PlayerId.PLAYER2


def _attack_names(player, state) -> list[str]:
    return [
        action.attack.name
        for action in player.get_actions(state)
        if isinstance(action, AttackAction)
    ]


def _charmander_with_attack_energy() -> PokemonCard:
    charmander = make_card("PAF-007")
    charmander.energy = [CardType.FIRE, CardType.FIRE]
    return charmander


def test_first_player_cannot_attack_on_turn_one():
    attacker = _charmander_with_attack_energy()
    state = make_state(
        PlayerZones(active=[attacker]),
        PlayerZones(active=[make_card("PAF-027")]),
        first_player_id=P1,
    )

    assert state.player1.firstTurn is True
    assert _attack_names(state.player1, state) == []


def test_second_player_can_attack_on_turn_one():
    attacker = _charmander_with_attack_energy()
    state = make_state(
        PlayerZones(active=[make_card("PAF-027")]),
        PlayerZones(active=[attacker]),
        turn=P2,
        first_player_id=P1,
    )

    assert state.player2.firstTurn is True
    assert _attack_names(state.player2, state) == [
        "Blazing Destruction",
        "Steady Firebreathing",
    ]


def test_supporter_lock_is_unchanged_on_turn_one():
    first_supporter = make_card("PAF-087")
    second_supporter = make_card("PAF-087")
    state = make_state(
        PlayerZones(active=[make_card("PAF-027")], hand=[first_supporter]),
        PlayerZones(active=[make_card("PAF-027")], hand=[second_supporter]),
        turn=P1,
        first_player_id=P1,
    )
    # The first player starts with supporterPlayedTurn=True; going second lifts it.
    state.player1.supporterPlayedTurn = True

    assert not [
        action
        for action in state.player1.get_actions(state)
        if isinstance(action, UseSupporterAction)
    ]

    state.turn = P2
    assert state.player2.supporterPlayedTurn is False
    assert [
        action
        for action in state.player2.get_actions(state)
        if isinstance(action, UseSupporterAction)
    ]


def test_evolution_first_turn_restriction_is_unchanged():
    for turn, player_attr in ((P1, "player1"), (P2, "player2")):
        charmander = make_card("PAF-007")
        charmander.firstTurnPlayed = False
        charmeleon = make_card("PAF-008")
        if turn == P1:
            p1_zones = PlayerZones(active=[charmander], hand=[charmeleon])
            p2_zones = PlayerZones(active=[make_card("PAF-027")])
        else:
            p1_zones = PlayerZones(active=[make_card("PAF-027")])
            p2_zones = PlayerZones(active=[charmander], hand=[charmeleon])
        state = make_state(p1_zones, p2_zones, turn=turn, first_player_id=P1)
        active_player = getattr(state, player_attr)

        assert active_player.firstTurn is True
        assert not [
            action
            for action in active_player.get_actions(state)
            if isinstance(action, EvolvePokemonAction)
        ]


def test_evolution_is_available_after_the_first_turn():
    charmander = make_card("PAF-007")
    charmander.firstTurnPlayed = False
    state = make_state(
        PlayerZones(active=[charmander], hand=[make_card("PAF-008")]),
        PlayerZones(active=[make_card("PAF-027")]),
        first_player_id=P1,
    )
    state.player1.firstTurn = False

    assert [
        action
        for action in state.player1.get_actions(state)
        if isinstance(action, EvolvePokemonAction)
    ]


def test_raichu_v_fast_charge_exception_still_applies_to_first_player():
    raichu = make_card("BRS-158")
    raichu.energy = [CardType.LIGHTNING]
    state = make_state(
        PlayerZones(active=[raichu]),
        PlayerZones(active=[make_card("PAF-027")]),
        first_player_id=P1,
    )

    assert _attack_names(state.player1, state) == ["Fast Charge"]


def test_environment_records_the_first_player_seat():
    env = PokemonTCG(seed=42, record_game=False)
    _obs, _reward, _done, info = env.reset()
    for _ in range(2):
        _obs, _reward, _done, info = env.step(info["raw_available_actions"][0])

    state = env.gamestate
    assert state.first_player_id == state.turn
    first_player = state.player1 if state.first_player_id == P1 else state.player2
    second_player = state.player1 if state.first_player_id == P2 else state.player2
    assert first_player.supporterPlayedTurn is True
    assert second_player.supporterPlayedTurn is False


def test_second_player_can_use_card_specific_attacks_on_turn_one():
    raichu = make_card("BRS-158")
    raichu.energy = [CardType.LIGHTNING, CardType.LIGHTNING]
    lugia = make_card("SIT-138")
    lugia.energy = [CardType.COLORLESS] * 4

    raichu_state = make_state(
        PlayerZones(active=[make_card("PAF-027")]),
        PlayerZones(active=[raichu]),
        turn=P2,
        first_player_id=P1,
    )
    lugia_state = make_state(
        PlayerZones(active=[make_card("PAF-027")]),
        PlayerZones(active=[lugia]),
        turn=P2,
        first_player_id=P1,
    )

    assert "Dynamic Spark" in _attack_names(raichu_state.player2, raichu_state)
    assert "Aero Dive" in _attack_names(lugia_state.player2, lugia_state)


def test_unknown_first_player_keeps_conservative_first_turn_lock():
    # States built directly without a recorded first-player seat keep the
    # historical lock instead of silently freeing both players to attack.
    attacker = _charmander_with_attack_energy()
    state = make_state(
        PlayerZones(active=[attacker]),
        PlayerZones(active=[make_card("PAF-027")]),
    )

    assert state.first_player_id is None
    assert state.player1.firstTurn is True
    assert _attack_names(state.player1, state) == []
