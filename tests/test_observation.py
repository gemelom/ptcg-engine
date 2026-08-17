from __future__ import annotations

from ptcg import PokemonTCG
from ptcg.core.enums import PlayerId
from tests.helpers.cards import make_card
from tests.helpers.state_builder import PlayerZones, make_state


def test_observation_hides_private_zones_and_is_detached_from_state():
    own_active = make_card("PAF-007")
    own_hand = make_card("SVE-002")
    opponent_active = make_card("PAF-054")
    opponent_hand = make_card("SVE-005")
    state = make_state(
        PlayerZones(
            hand=[own_hand],
            left=[make_card("SVE-004")],
            prize=[make_card("SVE-007")],
            active=[own_active],
        ),
        PlayerZones(
            hand=[opponent_hand],
            left=[make_card("SVE-008")],
            prize=[make_card("SVE-002")],
            active=[opponent_active],
        ),
        turn=PlayerId.PLAYER1,
    )

    observation = state.get_obs()

    assert observation["viewer"] == "player1"
    assert observation["self"]["hand"] == [own_hand.to_dict()]
    assert observation["opponent"]["hand"] is None
    assert observation["self"]["deck_count"] == 1
    assert observation["opponent"]["deck_count"] == 1
    assert observation["self"]["prize_count"] == 1
    assert observation["opponent"]["prize_count"] == 1
    assert "deck" not in observation["self"]
    assert "prize" not in observation["self"]

    observation["self"]["active"][0]["hp"] = "0"
    observation["self"]["hand"].clear()

    assert own_active.hp == 70
    assert state.player1.hand == [own_hand]


def test_observation_perspective_can_be_selected_explicitly():
    player1_hand = make_card("SVE-002")
    player2_hand = make_card("SVE-005")
    state = make_state(
        PlayerZones(hand=[player1_hand], active=[make_card("PAF-007")]),
        PlayerZones(hand=[player2_hand], active=[make_card("PAF-027")]),
    )

    observation = state.get_obs(PlayerId.PLAYER2)

    assert observation["viewer"] == "player2"
    assert observation["self"]["hand"] == [player2_hand.to_dict()]
    assert observation["opponent"]["hand"] is None


def test_full_state_is_only_exposed_with_explicit_debug_option():
    env = PokemonTCG(seed=42, record_game=False)
    _obs, _reward, _done, info = env.reset()

    assert "full_state" not in info

    debug_env = PokemonTCG(seed=42, record_game=False, expose_full_state=True)
    _obs, _reward, _done, debug_info = debug_env.reset()

    assert debug_info["full_state"] is debug_env.gamestate
